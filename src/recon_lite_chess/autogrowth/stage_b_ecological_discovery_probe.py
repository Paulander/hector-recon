"""Phase 2.9e sealed ecological discovery probe for Stage B / chase."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Mapping, Sequence

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .approach_discovery_probe import _after_move_repetition_key
from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .features import (
    extract_learner_features,
    learner_visible_key_firewall_leaks,
    validate_learner_visible_keys,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _evaluate_mate1_stage,
    _evaluate_mate2_stage,
    _train_mate1_stage,
    _train_mate2_stage,
    _unique,
)
from .quorum_basin import (
    _edge_mate_enter_mate2_audit,
    _edge_mate_fixed_seed_black_reply,
    _king_support_waypoint_geometry,
    _position_repetition_key,
    _white_rook_square,
    fence_established_geometry,
    load_canonical_mate2_first_scorer,
    load_chain_confidence_gate,
    run_krk_policy,
)
from .terminal_substrate import terminal_action_feature_keys


DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9e_ecological_discovery"
)
DEFAULT_STAGE_B_ROWS = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_b_rows.json"
)
DEFAULT_STAGE_A_ROWS = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9_overnight/stage_a_rows.json"
)
DEFAULT_STAGE_B_BASELINE_DIR = Path(
    "reports/autogrowth/clean_slate_krk/phase2_9a_action_firewall"
)

_ACTION_KEY_SCALE_CACHE: dict[tuple[str, str], tuple[tuple[str, float], ...]] = {}
_JudgeCache = tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]
_FAST_ENTER_MATE2_CACHE: dict[str, dict[str, Any]] = {}
_FAST_EXACT_MATE2_CACHE: dict[str, bool] = {}
_FAST_MATE1_CACHE: dict[str, bool] = {}


@dataclass(frozen=True)
class StageBEcologicalDiscoveryConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    stage_a_rows_path: str = str(DEFAULT_STAGE_A_ROWS)
    stage_b_rows_path: str = str(DEFAULT_STAGE_B_ROWS)
    stage_b_baseline_dir: str = str(DEFAULT_STAGE_B_BASELINE_DIR)
    seeds: tuple[int, ...] = (20272931, 20272932, 20272933)
    flat_baseline_seeds: tuple[int, ...] = (20272911, 20272912, 20272913)
    stage_a_train_row_limit: int | None = None
    train_row_limit: int | None = None
    heldout_row_limit: int | None = None
    horizon_plies: int = 16
    max_samples: int = 16
    max_population: int = 48
    max_total_population: int | None = None
    max_population_per_habitat: int = 2
    max_births_per_decision: int = 2
    max_guided_births: int = 48
    composite_width: int = 2
    max_child_pool: int = 16
    low_margin_threshold: float = 0.035
    conflict_abs_threshold: float = 0.05
    uncertainty_min_visits: int = 3
    uncertainty_low: float = 0.35
    uncertainty_high: float = 0.65
    novelty_seen_threshold: int = 1
    initial_nutrition: float = 0.34
    mature_nutrition: float = 1.10
    passive_decay: float = 0.010
    positive_credit: float = 0.16
    negative_debt: float = 0.18
    initial_weight: float = 0.050
    nutrition_weight_scale: float = 0.035
    max_advisory_weight: float = 0.180
    atom_score_scale: float = 1.0
    fast_exact_judge: bool = True
    ecology_mode: str = "global"
    stem_initial_xp: int = 50
    stem_mature_xp: int = 100
    stem_prune_xp: int = 0
    stem_min_mature_exposures: int = 3
    stem_inactive_decay_scale: float = 1.0
    max_mature_ablation_subjects: int = 8
    pruned_rescue_audit_limit: int = 8
    pruned_rescue_heldout_limit: int = 32
    native_foundation_key_mode: str = "coarse"
    native_foundation_max_ticks: int = 80
    native_foundation_train_repetitions: int = 5
    native_foundation_continuation_repetitions: int = 2
    native_foundation_max_mate1_positions: int | None = None
    native_foundation_max_mate2_positions: int | None = None
    native_foundation_prototype_scan_triplets: int = 512


def run_stage_b_ecological_discovery_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig()
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "design_spec.json", _design_spec(cfg))

    rows = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    train_rows = list(rows["train"])
    heldout_rows = list(rows["heldout"])
    if cfg.train_row_limit is not None:
        train_rows = train_rows[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        heldout_rows = heldout_rows[: int(cfg.heldout_row_limit)]

    references = _reference_baselines(cfg, heldout_rows)
    seed_results: dict[str, Any] = {}
    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        atom_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir)
            / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        arm1 = _run_arm(
            cfg,
            train_rows,
            heldout_rows,
            seed=seed,
            flat_seed=flat_seed,
            atom_weights=atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm1_unguided_ecological",
        )
        arm2 = _run_arm(
            cfg,
            train_rows,
            heldout_rows,
            seed=seed + 10_000,
            flat_seed=flat_seed,
            atom_weights=atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm2_guided_residual_control",
        )
        result = {
            "schema_version": "phase2_9e_stage_b_ecological_seed.v0",
            "seed": seed,
            "flat_baseline_seed": flat_seed,
            "arm1_unguided_ecological": arm1,
            "arm2_guided_residual_control": arm2,
            "paired_vs_yardsticks": {
                "arm1": _paired_yardstick_table(arm1["evaluations"]["survivor_trial"], references),
                "arm2": _paired_yardstick_table(arm2["evaluations"]["survivor_trial"], references),
            },
            "decision": _seed_decision(arm1, arm2),
        }
        _write_json(output_dir / f"seed_{seed}_result.json", result)
        seed_results[str(seed)] = result

    summary = {
        "schema_version": "phase2_9e_stage_b_ecological_discovery.v0",
        "config": asdict(cfg),
        "dataset": {
            "source_rows_path": str(cfg.stage_b_rows_path),
            "train_count": len(train_rows),
            "heldout_count": len(heldout_rows),
            "stage_labels_learner_visible": False,
            "exact_judge_birth_control": "forbidden_in_arm1_quarantined_to_arm2",
        },
        "reference_baselines": references,
        "seed_results": seed_results,
        "tables": _summary_tables(seed_results, references),
        "decision": _overall_decision(seed_results),
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_stage_b_ecological_discovery_scale_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase2_9f_ecological_scale",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
        train_row_limit=None,
        heldout_row_limit=None,
        max_population=4,
        max_guided_births=4,
        max_births_per_decision=1,
        max_samples=8,
    )
    summary = run_stage_b_ecological_discovery_probe(config=cfg)
    summary["schema_version"] = "phase2_9f_stage_b_ecological_scale.v0"
    summary["phase"] = "Phase 2.9f"
    summary["cross_seed_composite_analysis"] = _cross_seed_composite_analysis(summary["seed_results"])
    summary["enrichment_summary"] = _enrichment_summary(summary["seed_results"])
    summary["tables"]["phase2_9f_headline"] = _phase29f_headline(summary)
    _write_json(Path(cfg.output_dir) / "summary.json", summary)
    return summary


def run_stage_b_ecological_habitat_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase2_9g_habitat_ecology",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
        train_row_limit=None,
        heldout_row_limit=None,
        max_population=4,
        max_total_population=4,
        max_population_per_habitat=2,
        max_guided_births=8,
        max_births_per_decision=1,
        max_samples=8,
        ecology_mode="habitat_local",
    )
    summary = run_stage_b_ecological_discovery_probe(config=cfg)
    summary["schema_version"] = "phase2_9g_stage_b_habitat_ecology.v0"
    summary["phase"] = "Phase 2.9g"
    summary["cross_seed_composite_analysis"] = _cross_seed_composite_analysis(summary["seed_results"])
    summary["enrichment_summary"] = _enrichment_summary(summary["seed_results"])
    summary["tables"]["phase2_9g_headline"] = _phase29f_headline(summary)
    _write_json(Path(cfg.output_dir) / "summary.json", summary)
    return summary


def run_stage_b_graph_native_ecology_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_0_graph_native_ecology",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
        train_row_limit=None,
        heldout_row_limit=None,
        max_population_per_habitat=2,
        max_guided_births=8,
        max_births_per_decision=1,
        max_samples=8,
        ecology_mode="stem_cell_graph",
    )
    summary = run_stage_b_ecological_discovery_probe(config=cfg)
    summary["schema_version"] = "phase3_0_stage_b_graph_native_ecology.v0"
    summary["phase"] = "Phase 3.0"
    summary["cross_seed_composite_analysis"] = _cross_seed_composite_analysis(summary["seed_results"])
    summary["enrichment_summary"] = _enrichment_summary(summary["seed_results"])
    summary["maturity_summary"] = _maturity_summary(summary["seed_results"])
    summary["tables"]["phase3_0_headline"] = _phase30_headline(summary)
    _write_json(Path(cfg.output_dir) / "summary.json", summary)
    return summary


def run_stage_ab_graph_native_carryover_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_1_stage_ab_graph_native_carryover",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
        stage_a_train_row_limit=128,
        train_row_limit=128,
        heldout_row_limit=64,
        max_population_per_habitat=2,
        max_guided_births=8,
        max_births_per_decision=1,
        max_samples=8,
        pruned_rescue_audit_limit=4,
        ecology_mode="stem_cell_graph",
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_1_stage_ab_carryover_design_spec.v0"
    design["curriculum_carryover"] = {
        "scope": "Stage A warm-up followed by Stage B chase, same composite/stem-cell population",
        "not_claimed": "full Mate_In_1/Mate_In_2-to-StageB curriculum competence",
        "stage_labels_learner_visible": False,
    }
    design["discovery_boundary"]["learner_visible"] = [
        "board state",
        "legal moves",
        "sealed terminal_action_feature_keys",
        "stage-appropriate sealed flat atom weights for the scheduled training segment",
        "trial composite activations and local nutrition",
    ]
    _write_json(output_dir / "design_spec.json", design)

    stage_a_rows_payload = json.loads(Path(cfg.stage_a_rows_path).read_text(encoding="utf-8"))
    stage_b_rows_payload = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    stage_a_train_rows = list(stage_a_rows_payload["train"])
    stage_b_train_rows = list(stage_b_rows_payload["train"])
    heldout_rows = list(stage_b_rows_payload["heldout"])
    stage_a_limit = cfg.stage_a_train_row_limit if cfg.stage_a_train_row_limit is not None else cfg.train_row_limit
    if stage_a_limit is not None:
        stage_a_train_rows = stage_a_train_rows[: int(stage_a_limit)]
    if cfg.train_row_limit is not None:
        stage_b_train_rows = stage_b_train_rows[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        heldout_rows = heldout_rows[: int(cfg.heldout_row_limit)]

    references = _reference_baselines(cfg, heldout_rows)
    seed_results: dict[str, Any] = {}
    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        stage_a_atom_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir)
            / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_atom_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir)
            / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        training_segments = (
            {
                "name": "stage_a_approach_warmup",
                "rows": stage_a_train_rows,
                "atom_weights": stage_a_atom_weights,
                "success_kind": "approach_waypoint",
                "guided_births": False,
            },
            {
                "name": "stage_b_true_middle_chase",
                "rows": stage_b_train_rows,
                "atom_weights": stage_b_atom_weights,
                "success_kind": "stage_b_enter_mate2",
                "guided_births": True,
            },
        )
        arm1 = _run_arm_curriculum(
            cfg,
            training_segments,
            heldout_rows,
            seed=seed,
            flat_seed=flat_seed,
            final_atom_weights=stage_b_atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm1_unguided_ecological",
        )
        arm2 = _run_arm_curriculum(
            cfg,
            training_segments,
            heldout_rows,
            seed=seed + 10_000,
            flat_seed=flat_seed,
            final_atom_weights=stage_b_atom_weights,
            atom_eval_reference=references["sealed_flat_weight_replay"][str(flat_seed)],
            arm="arm2_guided_residual_control",
        )
        result = {
            "schema_version": "phase3_1_stage_ab_graph_native_carryover_seed.v0",
            "seed": seed,
            "flat_baseline_seed": flat_seed,
            "arm1_unguided_ecological": arm1,
            "arm2_guided_residual_control": arm2,
            "paired_vs_yardsticks": {
                "arm1": _paired_yardstick_table(arm1["evaluations"]["survivor_trial"], references),
                "arm2": _paired_yardstick_table(arm2["evaluations"]["survivor_trial"], references),
            },
            "decision": _seed_decision(arm1, arm2),
        }
        _write_json(output_dir / f"seed_{seed}_result.json", result)
        seed_results[str(seed)] = result

    summary = {
        "schema_version": "phase3_1_stage_ab_graph_native_carryover.v0",
        "phase": "Phase 3.1",
        "config": asdict(cfg),
        "dataset": {
            "stage_a_rows_path": str(cfg.stage_a_rows_path),
            "stage_b_rows_path": str(cfg.stage_b_rows_path),
            "stage_a_train_count": len(stage_a_train_rows),
            "stage_b_train_count": len(stage_b_train_rows),
            "stage_b_heldout_count": len(heldout_rows),
            "stage_labels_learner_visible": False,
            "same_population_across_stage_a_b": True,
            "full_foundation_curriculum": False,
        },
        "reference_baselines": references,
        "seed_results": seed_results,
        "tables": _summary_tables(seed_results, references),
        "cross_seed_composite_analysis": _cross_seed_composite_analysis(seed_results),
        "enrichment_summary": _enrichment_summary(seed_results),
        "maturity_summary": _maturity_summary(seed_results),
        "decision": _overall_decision(seed_results),
    }
    summary["tables"]["phase3_1_headline"] = _phase31_headline(summary)
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_stage_ab_native_foundation_ecology_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_2_native_foundation_ecology",
        seeds=(20272931, 20272932, 20272933),
        stage_a_train_row_limit=16,
        train_row_limit=16,
        heldout_row_limit=16,
        max_population_per_habitat=1,
        max_guided_births=0,
        max_births_per_decision=1,
        max_samples=6,
        pruned_rescue_audit_limit=2,
        pruned_rescue_heldout_limit=16,
        ecology_mode="stem_cell_graph",
        native_foundation_key_mode="coarse",
        native_foundation_prototype_scan_triplets=128,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_2_native_foundation_ecology_design_spec.v0"
    design["native_foundation_ecology"] = {
        "scope": "Mate_In_1/Mate_In_2 native foundation graph supplies the base move scores; ecological composites persist across Stage A then Stage B.",
        "not_claimed": "composites are not yet materialized as native ReCoN graph nodes inside the foundation graph",
        "stage_labels_learner_visible": False,
        "fallback_when_native_has_no_candidate": "random legal tie-break over zero base scores",
    }
    design["discovery_boundary"]["learner_visible"] = [
        "board state",
        "legal moves",
        "native same-graph Mate_In_1/Mate_In_2 confirmed action candidates and scores",
        "sealed terminal_action_feature_keys for spawned composite children",
        "trial composite activations and local nutrition",
    ]
    _write_json(output_dir / "design_spec.json", design)

    foundation = _train_native_foundation_for_ecology(cfg)
    native_graph = foundation["graph"]
    score_provider = _NativeFoundationScoreProvider(native_graph)

    stage_a_rows_payload = json.loads(Path(cfg.stage_a_rows_path).read_text(encoding="utf-8"))
    stage_b_rows_payload = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    stage_a_train_rows = list(stage_a_rows_payload["train"])
    stage_b_train_rows = list(stage_b_rows_payload["train"])
    heldout_rows = list(stage_b_rows_payload["heldout"])
    stage_a_limit = cfg.stage_a_train_row_limit if cfg.stage_a_train_row_limit is not None else cfg.train_row_limit
    if stage_a_limit is not None:
        stage_a_train_rows = stage_a_train_rows[: int(stage_a_limit)]
    if cfg.train_row_limit is not None:
        stage_b_train_rows = stage_b_train_rows[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        heldout_rows = heldout_rows[: int(cfg.heldout_row_limit)]

    references = _reference_baselines(cfg, heldout_rows)
    native_base_eval = _evaluate_policy(
        cfg,
        heldout_rows,
        lambda board, counts, row_id, ply, rng: _choose_base_score_move(
            board,
            counts,
            score_provider=score_provider,
            seed=20273100 + int(row_id) * 43 + ply,
        ),
        seed=20273100,
        policy_name="native_foundation_base_with_random_no_candidate_fallback",
    )
    references["native_foundation_base"] = native_base_eval
    native_coverage = {
        "stage_a_train": _native_foundation_coverage(score_provider, stage_a_train_rows),
        "stage_b_train": _native_foundation_coverage(score_provider, stage_b_train_rows),
        "stage_b_heldout": _native_foundation_coverage(score_provider, heldout_rows),
        "score_provider_cache": score_provider.stats(),
    }

    training_segments = (
        {
            "name": "stage_a_approach_warmup",
            "rows": stage_a_train_rows,
            "atom_weights": {},
            "base_score_provider": score_provider,
            "success_kind": "approach_waypoint",
            "guided_births": False,
        },
        {
            "name": "stage_b_true_middle_chase",
            "rows": stage_b_train_rows,
            "atom_weights": {},
            "base_score_provider": score_provider,
            "success_kind": "stage_b_enter_mate2",
            "guided_births": False,
        },
    )

    seed_results: dict[str, Any] = {}
    for seed in cfg.seeds:
        arm1 = _run_arm_curriculum(
            cfg,
            training_segments,
            heldout_rows,
            seed=seed,
            flat_seed=0,
            final_atom_weights={},
            final_base_score_provider=score_provider,
            atom_eval_reference=native_base_eval,
            arm="arm1_unguided_ecological",
        )
        arm2 = _run_arm_curriculum(
            cfg,
            training_segments,
            heldout_rows,
            seed=seed + 10_000,
            flat_seed=0,
            final_atom_weights={},
            final_base_score_provider=score_provider,
            atom_eval_reference=native_base_eval,
            arm="arm2_no_oracle_native_base_control",
        )
        result = {
            "schema_version": "phase3_2_native_foundation_ecology_seed.v0",
            "seed": seed,
            "native_foundation_key_mode": cfg.native_foundation_key_mode,
            "arm1_unguided_ecological": arm1,
            "arm2_no_oracle_native_base_control": arm2,
            "paired_vs_yardsticks": {
                "arm1": _paired_yardstick_table(arm1["evaluations"]["survivor_trial"], references),
                "arm2": _paired_yardstick_table(arm2["evaluations"]["survivor_trial"], references),
                "native_foundation_base": _paired_yardstick_table(native_base_eval, references),
            },
            "decision": _seed_decision(arm1, arm2),
        }
        _write_json(output_dir / f"seed_{seed}_result.json", result)
        seed_results[str(seed)] = result

    native_coverage["score_provider_cache_after_run"] = score_provider.stats()
    summary = {
        "schema_version": "phase3_2_native_foundation_ecology.v0",
        "phase": "Phase 3.2",
        "config": asdict(cfg),
        "dataset": {
            "stage_a_rows_path": str(cfg.stage_a_rows_path),
            "stage_b_rows_path": str(cfg.stage_b_rows_path),
            "stage_a_train_count": len(stage_a_train_rows),
            "stage_b_train_count": len(stage_b_train_rows),
            "stage_b_heldout_count": len(heldout_rows),
            "stage_labels_learner_visible": False,
            "same_native_foundation_graph_across_stage_a_b": True,
            "same_ecological_population_across_stage_a_b": True,
        },
        "native_foundation": foundation["summary"],
        "native_foundation_coverage": native_coverage,
        "reference_baselines": references,
        "seed_results": seed_results,
        "tables": _summary_tables(seed_results, references),
        "cross_seed_composite_analysis": _cross_seed_composite_analysis(seed_results),
        "enrichment_summary": _enrichment_summary(seed_results),
        "maturity_summary": _maturity_summary(seed_results),
        "decision": _overall_decision(seed_results),
    }
    summary["tables"]["phase3_2_headline"] = _phase32_headline(summary)
    _write_json(output_dir / "summary.json", summary)
    return summary


class _NativeFoundationScoreProvider:
    def __init__(self, graph: NativeReConKRKGraph) -> None:
        self.graph = graph
        self.cache: dict[str, dict[str, float]] = {}
        self.audit_count = 0
        self.cache_hit_count = 0
        self.candidate_row_count = 0
        self.confirmed_row_count = 0

    def __call__(self, board: chess.Board, counts: Mapping[Any, int]) -> Mapping[str, float]:
        del counts
        key = board.fen()
        cached = self.cache.get(key)
        if cached is not None:
            self.cache_hit_count += 1
            return cached
        self.audit_count += 1
        audit = self.graph.audit_choice(board)
        candidates = list(audit.get("confirmed_candidates", ()))
        self.candidate_row_count += int(int(audit.get("candidate_triplet_count", 0)) > 0)
        self.confirmed_row_count += int(bool(candidates))
        scores: dict[str, float] = {}
        for rank, item in enumerate(candidates):
            move = str(item["move"])
            score = max(0.05, 1.0 - 0.03 * rank)
            scores[move] = max(scores.get(move, 0.0), score)
        self.cache[key] = scores
        return scores

    def stats(self) -> dict[str, Any]:
        return {
            "audit_count": self.audit_count,
            "cache_hit_count": self.cache_hit_count,
            "cached_board_count": len(self.cache),
            "candidate_row_count": self.candidate_row_count,
            "confirmed_row_count": self.confirmed_row_count,
        }


def _train_native_foundation_for_ecology(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    native_cfg = NativeSingleGraphConfig(
        include_symmetries=True,
        train_repetitions=int(cfg.native_foundation_train_repetitions),
        continuation_repetitions=int(cfg.native_foundation_continuation_repetitions),
        max_ticks=int(cfg.native_foundation_max_ticks),
        max_samples=int(cfg.max_samples),
        key_mode=str(cfg.native_foundation_key_mode),
        prototype_distance_threshold=12,
        max_prototype_scan_triplets=int(cfg.native_foundation_prototype_scan_triplets),
        max_mate1_positions=cfg.native_foundation_max_mate1_positions,
        max_mate2_positions=cfg.native_foundation_max_mate2_positions,
    )
    entries = curated_stage_entries(include_symmetries=native_cfg.include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    mate2_buckets = _mate2_buckets(entries)
    mate2_fens = _unique(fen for bucket in mate2_buckets for fen in bucket["fens"])
    if native_cfg.max_mate1_positions is not None:
        mate1_fens = mate1_fens[: native_cfg.max_mate1_positions]
    if native_cfg.max_mate2_positions is not None:
        mate2_fens = mate2_fens[: native_cfg.max_mate2_positions]

    graph = NativeReConKRKGraph(config=native_cfg)
    mate1_training = _train_mate1_stage(graph, mate1_fens, config=native_cfg)
    mate1_eval = _evaluate_mate1_stage(graph, mate1_fens, config=native_cfg)
    maturation = graph.mature_existing_graph()
    mate2_training = _train_mate2_stage(graph, mate2_fens, config=native_cfg)
    mate2_eval = _evaluate_mate2_stage(graph, mate2_fens, config=native_cfg)
    if mate2_eval["conversion_rate"] >= native_cfg.mate2_threshold:
        graph.m4_event_count += 1
    summary = {
        "schema_version": "phase3_2_native_foundation_summary.v0",
        "config": asdict(native_cfg),
        "dataset": {
            "mate1_position_count": len(mate1_fens),
            "mate2_position_count": len(mate2_fens),
            "raw_mate2_bucket_entry_count": sum(len(bucket["fens"]) for bucket in mate2_buckets),
        },
        "mate1": {"training": mate1_training, "evaluation": mate1_eval},
        "maturation": maturation,
        "mate2": {"training": mate2_training, "evaluation": mate2_eval},
        "graph": graph.to_dict(),
        "decision": {
            "checkpoint_pass": (
                mate1_eval["accuracy"] >= native_cfg.mate1_threshold
                and mate2_eval["conversion_rate"] >= native_cfg.mate2_threshold
                and mate2_eval["same_graph_second_move_count"] > 0
            ),
            "same_native_graph_foundation": True,
            "key_mode": native_cfg.key_mode,
        },
    }
    return {"graph": graph, "summary": summary}


def _native_foundation_coverage(
    score_provider: _NativeFoundationScoreProvider,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    candidate_rows = 0
    samples: list[dict[str, Any]] = []
    for row in rows:
        board = chess.Board(str(row["fen"]))
        scores = score_provider(board, {})
        candidate_rows += int(bool(scores))
        if len(samples) < 4 and scores:
            samples.append(
                {
                    "row_id": int(row["row_id"]),
                    "scored_move_count": len(scores),
                    "top_moves": [
                        {"move": move, "score": round(float(score), 6)}
                        for move, score in sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)[:4]
                    ],
                }
            )
    return {
        "row_count": len(rows),
        "native_scored_row_count": candidate_rows,
        "native_scored_row_rate": candidate_rows / max(1, len(rows)),
        "samples": samples,
    }


def _design_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    return {
        "schema_version": "phase2_9e_design_spec.v0",
        "rung": "Stage B / true-middle chase stratum",
        "discovery_boundary": {
            "learner_visible": [
                "board state",
                "legal moves",
                "sealed terminal_action_feature_keys",
                "atom weights from sealed Stage B learner",
                "trial composite activations and local nutrition",
            ],
            "forbidden_for_arm1_birth": [
                "stage labels",
                "selector-owner ids",
                "hand chase features as causal features",
                "exact judge failures or success labels",
                "human-selected spawn sites",
                "global top-K promotion",
            ],
            "exact_judge_use": "after-the-fact rollout outcome and heldout ablation only",
        },
        "arms": {
            "arm1_unguided_ecological": (
                "Births use learner-internal triggers only: low margin, active atom "
                "conflict, novel percept signatures, repeated trace uncertainty, and "
                "yoked random births. Survival uses local credit/debt plus passive decay; "
                "habitat-local mode restricts decay and competition to revisited percept "
                "signatures; graph-native mode stores composites as StemCellTerminal "
                "TRIAL/MATURE/PRUNED cells with parent-local resource accounting."
            ),
            "arm2_guided_residual_control": (
                "Quarantined expressivity probe. Births are aimed at atom-only failure "
                "rows and must not be counted as autogrowth evidence."
            ),
        },
        "stop_rules": [
            "Arm1 population collapse-to-zero after nonzero births",
            "Arm1 cap pressure on more than half of train decisions",
            "Arm1 load-bearing count remains zero across all seeds",
        ],
        "config": asdict(cfg),
    }


def _run_arm(
    cfg: StageBEcologicalDiscoveryConfig,
    train_rows: Sequence[Mapping[str, Any]],
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    flat_seed: int,
    atom_weights: Mapping[str, float],
    atom_eval_reference: Mapping[str, Any],
    arm: str,
) -> dict[str, Any]:
    rng = random.Random(seed)
    population: dict[str, dict[str, Any]] = {}
    stem_cells: dict[str, StemCellTerminal] = {}
    seen_signatures: Counter[str] = Counter()
    signature_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    trigger_counts: Counter[str] = Counter()
    birth_curve: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    train_judge_cache = _new_judge_cache()
    early_stop_reason: str | None = None
    processed_train_count = 0
    guided_plan = (
        _guided_residual_birth_plan(cfg, train_rows, atom_weights, seed=seed)
        if arm == "arm2_guided_residual_control"
        else {}
    )

    for step, row in enumerate(train_rows):
        processed_train_count = step + 1
        if arm == "arm2_guided_residual_control":
            _spawn_guided_for_row(
                cfg,
                population,
                row,
                guided_plan.get(int(row["row_id"]), ()),
                step=step,
                seed=seed,
                trigger_counts=trigger_counts,
                stem_cells=stem_cells,
            )

        selected = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=atom_weights,
                population=population,
                seed=seed + int(row_id) * 37 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
                spawn_hook=(
                    None
                    if arm == "arm2_guided_residual_control"
                    else lambda ctx: _spawn_arm1_from_context(
                        cfg,
                        population,
                        ctx,
                        seen_signatures=seen_signatures,
                        signature_outcomes=signature_outcomes,
                        trigger_counts=trigger_counts,
                        rng=rng,
                        stem_cells=stem_cells,
                    )
                ),
            ),
            seed=seed + step * 31,
            collect_composites=True,
            population=population,
            judge_cache=train_judge_cache,
        )
        alternative = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_atom_move(
                board,
                counts,
                atom_weights=atom_weights,
                seed=seed + 50_000 + int(row_id) * 37 + ply,
            ),
            seed=seed + 100_000 + step * 31,
            collect_composites=True,
            population=population,
            judge_cache=train_judge_cache,
        )
        if cfg.ecology_mode == "stem_cell_graph":
            _apply_stem_cell_local_economy(
                cfg,
                population,
                stem_cells,
                selected=selected,
                alternative=alternative,
                step=step,
            )
        else:
            _apply_contrastive_nutrition(
                cfg,
                population,
                selected=selected,
                alternative=alternative,
                step=step,
            )
        for signature in selected["percept_signatures"]:
            signature_outcomes[signature]["success" if selected["success"] else "failure"] += 1
        if cfg.ecology_mode == "stem_cell_graph":
            _cap_stem_cell_parent_budgets(cfg, population, stem_cells, step=step)
        else:
            _cap_population(cfg, population, step=step)
        if step % 25 == 0 or step == len(train_rows) - 1:
            birth_curve.append(_population_snapshot(population, step=step))
        if len(traces) < cfg.max_samples:
            traces.append(
                {
                    "row_id": int(row["row_id"]),
                    "selected_endpoint": selected["endpoint"],
                    "selected_success": bool(selected["success"]),
                    "alternative_endpoint": alternative["endpoint"],
                    "alternative_success": bool(alternative["success"]),
                    "reward_delta": selected["reward"] - alternative["reward"],
                    "active_composite_count": len(selected["active_composite_ids"]),
                }
            )
        if population and not any(item["state"] in {"TRIAL", "MATURE"} for item in population.values()):
            early_stop_reason = "population_collapse_to_zero"
            if not birth_curve or birth_curve[-1]["step"] != step:
                birth_curve.append(_population_snapshot(population, step=step))
            break

    survivors = [dict(item) for item in population.values() if item["state"] in {"TRIAL", "MATURE"}]
    survivors.sort(key=lambda item: (-float(item["nutrition"]), item["composite_id"]))
    if cfg.ecology_mode == "stem_cell_graph":
        mature_subjects = [dict(item) for item in survivors if item.get("state") == "MATURE"]
        mature_subjects.sort(
            key=lambda item: (
                float(item.get("local_resource", item.get("nutrition", 0.0))),
                int(item.get("stem_cell_xp") or 0),
                int(item.get("activation_count", 0)),
                str(item["composite_id"]),
            ),
            reverse=True,
        )
        ablation_subjects = mature_subjects[: max(0, int(cfg.max_mature_ablation_subjects))]
    else:
        ablation_subjects = survivors
    structure = _structure_summary(
        cfg,
        arm=arm,
        seed=seed,
        flat_seed=flat_seed,
        atom_weights=atom_weights,
        population=population,
        survivors=survivors,
        trigger_counts=trigger_counts,
        guided_plan=guided_plan,
        processed_train_count=processed_train_count,
        early_stop_reason=early_stop_reason,
    )
    health = _composite_ablation_health(
        cfg,
        heldout_rows,
        atom_weights=atom_weights,
        composites=ablation_subjects,
        seed=seed + 700,
        policy_name=f"{arm}_survivor_trial",
    )
    pruned_rescue_audit = (
        _pruned_rescue_audit(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            survivors=ablation_subjects,
            population=population,
            survivor_eval=health["full_evaluation"],
            seed=seed + 760,
        )
        if cfg.ecology_mode == "stem_cell_graph" and arm == "arm1_unguided_ecological"
        else {"enabled": False}
    )
    promoted = [
        dict(item, m4_state="MATURE", heldout_counterfactual_delta=int(record["ablation_delta"]))
        for item in survivors
        for record in health["records"]
        if record["composite_id"] == item["composite_id"] and int(record["ablation_delta"]) > 0
    ]
    pruned_harmful = [
        str(record["composite_id"])
        for record in health["records"]
        if int(record["ablation_delta"]) < 0
    ]
    survivor_eval = health["full_evaluation"]
    atom_eval = {**atom_eval_reference, "policy": f"{arm}_atom_only_replay"}
    if promoted:
        promoted_eval = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=atom_weights,
                population={item["composite_id"]: item for item in promoted},
                seed=seed + int(row_id) * 41 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
            ),
            seed=seed + 900,
            policy_name=f"{arm}_promoted_positive_only",
        )
    else:
        promoted_eval = {**atom_eval, "policy": f"{arm}_promoted_positive_only"}
    enrichment = _survivor_failure_enrichment(
        cfg,
        heldout_rows,
        atom_weights=atom_weights,
        composites=ablation_subjects,
        atom_eval=atom_eval,
        seed=seed + 990,
    )
    collapse = bool(structure["birth_count"] > 0 and structure["survivor_count"] == 0)
    population_limit = cfg.max_total_population or cfg.max_population
    explosion = bool(structure["survivor_count"] > population_limit * 2)
    return {
        "schema_version": "phase2_9e_arm_result.v0",
        "arm": arm,
        "seed": seed,
        "flat_baseline_seed": flat_seed,
        "autogrowth_evidence": arm == "arm1_unguided_ecological",
        "uses_oracle_birth": arm == "arm2_guided_residual_control",
        "structure": structure,
        "birth_death_curve": birth_curve,
        "train_trace_sample": traces,
        "post_hoc_ablation_subject": (
            "top_mature_composites_by_local_resource"
            if cfg.ecology_mode == "stem_cell_graph"
            else "all_live_survivors"
        ),
        "post_hoc_ablation_subject_count": len(ablation_subjects),
        "post_hoc_ablation_subject_limit": (
            int(cfg.max_mature_ablation_subjects) if cfg.ecology_mode == "stem_cell_graph" else None
        ),
        "post_hoc_ablation": health,
        "promotion": {
            "rule": "promote_positive_heldout_counterfactual_delta_only",
            "promoted_count": len(promoted),
            "pruned_negative_ablation_delta_count": len(pruned_harmful),
            "pruned_negative_ablation_delta_ids": pruned_harmful[: cfg.max_samples],
        },
        "evaluations": {
            "atom_only_replay": atom_eval,
            "survivor_trial": survivor_eval,
            "promoted_positive_only": promoted_eval,
        },
        "post_hoc_failure_enrichment": enrichment,
        "pruned_rescue_audit": pruned_rescue_audit,
        "candidate_fate_log": _candidate_fate_log(population) if cfg.ecology_mode == "stem_cell_graph" else [],
        "survivor_composite_dumps": _survivor_dumps(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            composites=ablation_subjects,
            health=health,
            seed=seed + 1_025,
        ),
        "load_bearing_composite_dumps": _load_bearing_dumps(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            composites=ablation_subjects,
            health=health,
            seed=seed + 1_050,
        ),
        "stop_rule": {
            "population_collapse_to_zero": collapse,
            "unbounded_explosion_cap_pressure": explosion,
        },
    }


def _run_arm_curriculum(
    cfg: StageBEcologicalDiscoveryConfig,
    training_segments: Sequence[Mapping[str, Any]],
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    flat_seed: int,
    final_atom_weights: Mapping[str, float],
    atom_eval_reference: Mapping[str, Any],
    arm: str,
    final_base_score_provider: Any | None = None,
) -> dict[str, Any]:
    rng = random.Random(seed)
    population: dict[str, dict[str, Any]] = {}
    stem_cells: dict[str, StemCellTerminal] = {}
    seen_signatures: Counter[str] = Counter()
    signature_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    trigger_counts: Counter[str] = Counter()
    birth_curve: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    train_judge_cache = _new_judge_cache()
    early_stop_reason: str | None = None
    processed_train_count = 0
    segment_summaries: list[dict[str, Any]] = []
    guided_plans: dict[str, Mapping[int, Sequence[Mapping[str, Any]]]] = {}
    for segment in training_segments:
        name = str(segment["name"])
        rows = list(segment["rows"])
        weights = segment["atom_weights"]
        success_kind = str(segment.get("success_kind", "stage_b_enter_mate2"))
        guided_plans[name] = (
            _guided_residual_birth_plan(cfg, rows, weights, seed=seed, success_kind=success_kind)
            if arm == "arm2_guided_residual_control" and bool(segment.get("guided_births", False))
            else {}
        )

    for segment in training_segments:
        segment_name = str(segment["name"])
        rows = list(segment["rows"])
        atom_weights = segment["atom_weights"]
        base_score_provider = segment.get("base_score_provider")
        success_kind = str(segment.get("success_kind", "stage_b_enter_mate2"))
        segment_start_births = len(population)
        segment_start_pruned = sum(1 for item in population.values() if item["state"] == "PRUNED")
        segment_start_mature = sum(1 for item in population.values() if item["state"] == "MATURE")
        for local_step, row in enumerate(rows):
            global_step = processed_train_count
            processed_train_count += 1
            if arm == "arm2_guided_residual_control":
                _spawn_guided_for_row(
                    cfg,
                    population,
                    row,
                    guided_plans.get(segment_name, {}).get(int(row["row_id"]), ()),
                    step=global_step,
                    seed=seed,
                    trigger_counts=trigger_counts,
                    stem_cells=stem_cells,
                    birth_segment=segment_name,
                )

            selected = _rollout_policy(
                cfg,
                row,
                lambda board, counts, row_id, ply, rng, segment_name=segment_name: _choose_ecological_move(
                    cfg,
                    board,
                    counts,
                    atom_weights=atom_weights,
                    population=population,
                    base_move_scores=_call_base_score_provider(base_score_provider, board, counts),
                    seed=seed + int(row_id) * 37 + ply,
                    disabled_composite_ids=set(),
                    row_id=row_id,
                    ply=global_step * max(1, cfg.horizon_plies) + ply,
                    segment_name=segment_name,
                    spawn_hook=(
                        None
                        if arm == "arm2_guided_residual_control"
                        else lambda ctx: _spawn_arm1_from_context(
                            cfg,
                            population,
                            ctx,
                            seen_signatures=seen_signatures,
                            signature_outcomes=signature_outcomes,
                            trigger_counts=trigger_counts,
                            rng=rng,
                            stem_cells=stem_cells,
                        )
                    ),
                ),
                seed=seed + global_step * 31,
                collect_composites=True,
                population=population,
                judge_cache=train_judge_cache,
                success_kind=success_kind,
            )
            alternative = _rollout_policy(
                cfg,
                row,
                (
                    lambda board, counts, row_id, ply, rng: _choose_base_score_move(
                        board,
                        counts,
                        score_provider=base_score_provider,
                        seed=seed + 50_000 + int(row_id) * 37 + ply,
                    )
                )
                if base_score_provider is not None
                else lambda board, counts, row_id, ply, rng: _choose_atom_move(
                        board,
                        counts,
                        atom_weights=atom_weights,
                        seed=seed + 50_000 + int(row_id) * 37 + ply,
                    ),
                seed=seed + 100_000 + global_step * 31,
                collect_composites=True,
                population=population,
                judge_cache=train_judge_cache,
                success_kind=success_kind,
            )
            if cfg.ecology_mode == "stem_cell_graph":
                _apply_stem_cell_local_economy(
                    cfg,
                    population,
                    stem_cells,
                    selected=selected,
                    alternative=alternative,
                    step=global_step,
                )
            else:
                _apply_contrastive_nutrition(
                    cfg,
                    population,
                    selected=selected,
                    alternative=alternative,
                    step=global_step,
                )
            for signature in selected["percept_signatures"]:
                signature_outcomes[signature]["success" if selected["success"] else "failure"] += 1
            if cfg.ecology_mode == "stem_cell_graph":
                _cap_stem_cell_parent_budgets(cfg, population, stem_cells, step=global_step)
            else:
                _cap_population(cfg, population, step=global_step)
            if global_step % 25 == 0 or local_step == len(rows) - 1:
                snapshot = _population_snapshot(population, step=global_step)
                snapshot["segment"] = segment_name
                birth_curve.append(snapshot)
            if len(traces) < cfg.max_samples:
                traces.append(
                    {
                        "segment": segment_name,
                        "row_id": int(row["row_id"]),
                        "selected_endpoint": selected["endpoint"],
                        "selected_success": bool(selected["success"]),
                        "alternative_endpoint": alternative["endpoint"],
                        "alternative_success": bool(alternative["success"]),
                        "reward_delta": selected["reward"] - alternative["reward"],
                        "active_composite_count": len(selected["active_composite_ids"]),
                    }
                )
            if population and not any(item["state"] in {"TRIAL", "MATURE"} for item in population.values()):
                early_stop_reason = f"population_collapse_to_zero:{segment_name}"
                if not birth_curve or birth_curve[-1]["step"] != global_step:
                    snapshot = _population_snapshot(population, step=global_step)
                    snapshot["segment"] = segment_name
                    birth_curve.append(snapshot)
                break
        segment_summaries.append(
            {
                "name": segment_name,
                "success_kind": success_kind,
                "row_count": len(rows),
                "births_after_segment": len(population),
                "births_during_segment": len(population) - segment_start_births,
                "mature_after_segment": sum(1 for item in population.values() if item["state"] == "MATURE"),
                "mature_delta": sum(1 for item in population.values() if item["state"] == "MATURE") - segment_start_mature,
                "pruned_after_segment": sum(1 for item in population.values() if item["state"] == "PRUNED"),
                "pruned_delta": sum(1 for item in population.values() if item["state"] == "PRUNED") - segment_start_pruned,
            }
        )
        if early_stop_reason is not None:
            break

    survivors = [dict(item) for item in population.values() if item["state"] in {"TRIAL", "MATURE"}]
    survivors.sort(key=lambda item: (-float(item["nutrition"]), item["composite_id"]))
    if cfg.ecology_mode == "stem_cell_graph":
        mature_subjects = [dict(item) for item in survivors if item.get("state") == "MATURE"]
        mature_subjects.sort(
            key=lambda item: (
                float(item.get("local_resource", item.get("nutrition", 0.0))),
                int(item.get("stem_cell_xp") or 0),
                int(item.get("activation_count", 0)),
                str(item["composite_id"]),
            ),
            reverse=True,
        )
        ablation_subjects = mature_subjects[: max(0, int(cfg.max_mature_ablation_subjects))]
    else:
        ablation_subjects = survivors
    merged_guided_plan: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for plan in guided_plans.values():
        for row_id, items in plan.items():
            merged_guided_plan[int(row_id)].extend(items)
    structure = _structure_summary(
        cfg,
        arm=arm,
        seed=seed,
        flat_seed=flat_seed,
        atom_weights=final_atom_weights,
        population=population,
        survivors=survivors,
        trigger_counts=trigger_counts,
        guided_plan=merged_guided_plan,
        processed_train_count=processed_train_count,
        early_stop_reason=early_stop_reason,
    )
    structure["curriculum_carryover"] = {
        "same_population_across_segments": True,
        "segments": segment_summaries,
        "births_by_segment": dict(sorted(Counter(str(item.get("birth_segment", "unknown")) for item in population.values()).items())),
        "survivors_by_birth_segment": dict(
            sorted(Counter(str(item.get("birth_segment", "unknown")) for item in survivors).items())
        ),
    }
    health = _composite_ablation_health(
        cfg,
        heldout_rows,
        atom_weights=final_atom_weights,
        base_score_provider=final_base_score_provider,
        composites=ablation_subjects,
        seed=seed + 700,
        policy_name=f"{arm}_stage_b_survivor_trial_after_stage_a_carryover",
    )
    pruned_rescue_audit = (
        _pruned_rescue_audit(
            cfg,
            heldout_rows,
            atom_weights=final_atom_weights,
            base_score_provider=final_base_score_provider,
            survivors=ablation_subjects,
            population=population,
            survivor_eval=health["full_evaluation"],
            seed=seed + 760,
        )
        if cfg.ecology_mode == "stem_cell_graph" and arm == "arm1_unguided_ecological"
        else {"enabled": False}
    )
    promoted = [
        dict(item, m4_state="MATURE", heldout_counterfactual_delta=int(record["ablation_delta"]))
        for item in survivors
        for record in health["records"]
        if record["composite_id"] == item["composite_id"] and int(record["ablation_delta"]) > 0
    ]
    pruned_harmful = [
        str(record["composite_id"])
        for record in health["records"]
        if int(record["ablation_delta"]) < 0
    ]
    survivor_eval = health["full_evaluation"]
    atom_eval = {**atom_eval_reference, "policy": f"{arm}_stage_b_atom_only_replay"}
    if promoted:
        promoted_eval = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=final_atom_weights,
                population={item["composite_id"]: item for item in promoted},
                base_move_scores=_call_base_score_provider(final_base_score_provider, board, counts),
                seed=seed + int(row_id) * 41 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
            ),
            seed=seed + 900,
            policy_name=f"{arm}_stage_b_promoted_positive_only",
        )
    else:
        promoted_eval = {**atom_eval, "policy": f"{arm}_stage_b_promoted_positive_only"}
    enrichment = _survivor_failure_enrichment(
        cfg,
        heldout_rows,
        atom_weights=final_atom_weights,
        base_score_provider=final_base_score_provider,
        composites=ablation_subjects,
        atom_eval=atom_eval,
        seed=seed + 990,
    )
    collapse = bool(structure["birth_count"] > 0 and structure["survivor_count"] == 0)
    population_limit = cfg.max_total_population or cfg.max_population
    explosion = bool(structure["survivor_count"] > population_limit * 2)
    return {
        "schema_version": "phase3_1_curriculum_arm_result.v0",
        "arm": arm,
        "seed": seed,
        "flat_baseline_seed": flat_seed,
        "autogrowth_evidence": arm == "arm1_unguided_ecological",
        "uses_oracle_birth": arm == "arm2_guided_residual_control",
        "curriculum_carryover": {
            "same_population_across_segments": True,
            "segments": segment_summaries,
            "final_eval_segment": "stage_b_true_middle_chase",
        },
        "structure": structure,
        "birth_death_curve": birth_curve,
        "train_trace_sample": traces,
        "post_hoc_ablation_subject": (
            "top_mature_composites_by_local_resource"
            if cfg.ecology_mode == "stem_cell_graph"
            else "all_live_survivors"
        ),
        "post_hoc_ablation_subject_count": len(ablation_subjects),
        "post_hoc_ablation_subject_limit": (
            int(cfg.max_mature_ablation_subjects) if cfg.ecology_mode == "stem_cell_graph" else None
        ),
        "post_hoc_ablation": health,
        "promotion": {
            "rule": "promote_positive_heldout_counterfactual_delta_only",
            "promoted_count": len(promoted),
            "pruned_negative_ablation_delta_count": len(pruned_harmful),
            "pruned_negative_ablation_delta_ids": pruned_harmful[: cfg.max_samples],
        },
        "evaluations": {
            "atom_only_replay": atom_eval,
            "survivor_trial": survivor_eval,
            "promoted_positive_only": promoted_eval,
        },
        "post_hoc_failure_enrichment": enrichment,
        "pruned_rescue_audit": pruned_rescue_audit,
        "candidate_fate_log": _candidate_fate_log(population) if cfg.ecology_mode == "stem_cell_graph" else [],
        "survivor_composite_dumps": _survivor_dumps(
            cfg,
            heldout_rows,
            atom_weights=final_atom_weights,
            composites=ablation_subjects,
            health=health,
            seed=seed + 1_025,
        ),
        "load_bearing_composite_dumps": _load_bearing_dumps(
            cfg,
            heldout_rows,
            atom_weights=final_atom_weights,
            composites=ablation_subjects,
            health=health,
            seed=seed + 1_050,
        ),
        "stop_rule": {
            "population_collapse_to_zero": collapse,
            "unbounded_explosion_cap_pressure": explosion,
        },
    }


def _spawn_arm1_from_context(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    ctx: Mapping[str, Any],
    *,
    seen_signatures: Counter[str],
    signature_outcomes: Mapping[str, Counter[str]],
    trigger_counts: Counter[str],
    rng: random.Random,
    stem_cells: dict[str, StemCellTerminal] | None = None,
) -> None:
    triggers = _internal_triggers(cfg, ctx, seen_signatures, signature_outcomes)
    signature = str(ctx["percept_signature"])
    seen_signatures[signature] += 1
    if not triggers:
        return
    spawned = 0
    for trigger in triggers:
        if spawned >= cfg.max_births_per_decision:
            break
        if _spawn_composite(
            cfg,
            population,
            _candidate_child_pool(ctx, trigger=trigger),
            trigger=trigger,
            arm="arm1_unguided_ecological",
            birth_step=int(ctx["step"]),
            birth_row_id=int(ctx["row_id"]),
            rng=rng,
            oracle_targeted=False,
            source_signature=signature,
            stem_cells=stem_cells,
            birth_segment=str(ctx.get("segment", "")) or None,
        ):
            trigger_counts[trigger] += 1
            spawned += 1
    for _ in range(spawned):
        random_option = rng.choice(list(ctx["options"]))
        if _spawn_composite(
            cfg,
            population,
            _generic_child_pool(random_option["active_keys"]),
            trigger="random_yoked_birth",
            arm="arm1_unguided_ecological",
            birth_step=int(ctx["step"]),
            birth_row_id=int(ctx["row_id"]),
            rng=rng,
            oracle_targeted=False,
            source_signature=signature,
            stem_cells=stem_cells,
            birth_segment=str(ctx.get("segment", "")) or None,
        ):
            trigger_counts["random_yoked_birth"] += 1
    if cfg.ecology_mode == "stem_cell_graph":
        _cap_stem_cell_parent_budgets(cfg, population, stem_cells or {}, step=int(ctx["step"]))
    else:
        _cap_population(cfg, population, step=int(ctx["step"]))


def _internal_triggers(
    cfg: StageBEcologicalDiscoveryConfig,
    ctx: Mapping[str, Any],
    seen_signatures: Counter[str],
    signature_outcomes: Mapping[str, Counter[str]],
) -> list[str]:
    triggers: list[str] = []
    margin = float(ctx["margin"])
    top = ctx["top_option"]
    if margin <= cfg.low_margin_threshold:
        triggers.append("low_margin_action_ranking")
    if (
        abs(float(top["positive_score"])) >= cfg.conflict_abs_threshold
        and abs(float(top["negative_score"])) >= cfg.conflict_abs_threshold
    ):
        triggers.append("conflicting_active_atoms")
    signature = str(ctx["percept_signature"])
    if int(seen_signatures[signature]) <= cfg.novelty_seen_threshold:
        triggers.append("novel_percept_signature")
    outcomes = signature_outcomes.get(signature, Counter())
    visits = int(outcomes["success"] + outcomes["failure"])
    if visits >= cfg.uncertainty_min_visits:
        rate = outcomes["success"] / max(1, visits)
        if cfg.uncertainty_low <= rate <= cfg.uncertainty_high:
            triggers.append("repeated_local_trace_uncertainty")
    return triggers


def _spawn_guided_for_row(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    row: Mapping[str, Any],
    plans: Sequence[Mapping[str, Any]],
    *,
    step: int,
    seed: int,
    trigger_counts: Counter[str],
    stem_cells: dict[str, StemCellTerminal] | None = None,
    birth_segment: str | None = None,
) -> None:
    if not plans:
        return
    rng = random.Random(seed + int(row["row_id"]) * 101)
    for plan in plans:
        if _spawn_composite(
            cfg,
            population,
            plan["active_keys"],
            trigger="oracle_atom_failure_residual",
            arm="arm2_guided_residual_control",
            birth_step=step,
            birth_row_id=int(row["row_id"]),
            rng=rng,
            oracle_targeted=True,
            source_signature=str(plan["source_signature"]),
            target_move=str(plan["target_move"]),
            stem_cells=stem_cells,
            birth_segment=birth_segment,
        ):
            trigger_counts["oracle_atom_failure_residual"] += 1
    if cfg.ecology_mode == "stem_cell_graph":
        _cap_stem_cell_parent_budgets(cfg, population, stem_cells or {}, step=step)
    else:
        _cap_population(cfg, population, step=step)


def _spawn_composite(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    child_pool: Iterable[str],
    *,
    trigger: str,
    arm: str,
    birth_step: int,
    birth_row_id: int,
    rng: random.Random,
    oracle_targeted: bool,
    source_signature: str,
    target_move: str | None = None,
    stem_cells: dict[str, StemCellTerminal] | None = None,
    birth_segment: str | None = None,
) -> bool:
    pool = tuple(dict.fromkeys(key for key in child_pool if not learner_visible_key_firewall_leaks([key])))
    if len(pool) < cfg.composite_width:
        return False
    combos = list(combinations(pool[: cfg.max_child_pool], cfg.composite_width))
    if not combos:
        return False
    children = tuple(sorted(rng.choice(combos)))
    if all(child.startswith("before_terminal:") for child in children):
        return False
    composite_id = _composite_id(arm, children)
    if composite_id in population:
        return False
    stem_cell: StemCellTerminal | None = None
    parent_id = _stem_parent_id(source_signature)
    if cfg.ecology_mode == "stem_cell_graph":
        stem_cell = _new_composite_stem_cell(
            cfg,
            composite_id=composite_id,
            children=children,
            parent_id=parent_id,
            source_signature=source_signature,
            trigger=trigger,
            arm=arm,
            birth_step=birth_step,
        )
        if stem_cells is not None:
            stem_cells[composite_id] = stem_cell
    population[composite_id] = {
        "composite_id": composite_id,
        "node_type": "SCRIPT",
        "confirm_policy": "k_of_n",
        "k": len(children),
        "n": len(children),
        "children": list(children),
        "arm": arm,
        "birth_trigger": trigger,
        "birth_segment": birth_segment,
        "birth_step": birth_step,
        "birth_row_id": birth_row_id,
        "parent_id": parent_id,
        "source_signature": source_signature,
        "target_move": target_move,
        "oracle_targeted_birth": oracle_targeted,
        "nutrition": cfg.initial_nutrition,
        "local_resource": cfg.initial_nutrition,
        "state": stem_cell.state.name if stem_cell is not None else "TRIAL",
        "stem_cell_id": stem_cell.cell_id if stem_cell is not None else None,
        "stem_cell_xp": stem_cell.xp if stem_cell is not None else None,
        "credit_events": 0,
        "debt_events": 0,
        "neutral_events": 0,
        "exposure_count": 0,
        "passive_decay_events": 0,
        "activation_count": 0,
        "weight": cfg.initial_weight,
        "fate_events": [
            {
                "step": birth_step,
                "event": "birth",
                "parent_id": parent_id,
                "source_signature": source_signature,
                "trigger": trigger,
                "birth_segment": birth_segment,
                "state": stem_cell.state.name if stem_cell is not None else "TRIAL",
                "xp": stem_cell.xp if stem_cell is not None else None,
                "local_resource": cfg.initial_nutrition,
            }
        ] if cfg.ecology_mode == "stem_cell_graph" else [],
    }
    return True


def _stem_parent_id(source_signature: str) -> str:
    digest = hashlib.sha256(str(source_signature).encode("utf-8")).hexdigest()
    return f"stage_b_habitat_{digest[:12]}"


def _new_composite_stem_cell(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    composite_id: str,
    children: Sequence[str],
    parent_id: str,
    source_signature: str,
    trigger: str,
    arm: str,
    birth_step: int,
) -> StemCellTerminal:
    cell = StemCellTerminal(f"stem_{composite_id}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = parent_id
    cell.xp = int(cfg.stem_initial_xp)
    cell.XP_SOLIDIFY = int(cfg.stem_mature_xp)
    cell.is_composition = True
    cell.children = list(children)
    cell.depth = 1
    cell.metadata.update(
        {
            "origin": "phase3_0_stage_b_graph_native_ecology",
            "composite_id": composite_id,
            "source_signature": source_signature,
            "birth_trigger": trigger,
            "birth_step": birth_step,
            "arm": arm,
            "lifecycle_substrate": "StemCellTerminal",
        }
    )
    return cell


def _sync_stem_cell_record(item: dict[str, Any], cell: StemCellTerminal) -> None:
    item["state"] = cell.state.name
    item["stem_cell_xp"] = int(cell.xp)
    item["stem_cell_snapshot"] = {
        "cell_id": cell.cell_id,
        "state": cell.state.name,
        "xp": int(cell.xp),
        "trial_parent_id": cell.trial_parent_id,
        "candidate_stats": cell.candidate_stats.to_dict(),
        "children": list(cell.children),
        "is_composition": bool(cell.is_composition),
    }


def _record_fate_event(
    item: dict[str, Any],
    *,
    step: int,
    event: str,
    cell: StemCellTerminal | None = None,
    **payload: Any,
) -> None:
    record = {
        "step": int(step),
        "event": event,
        "state": item.get("state"),
        "xp": item.get("stem_cell_xp"),
        "local_resource": round(float(item.get("local_resource", item.get("nutrition", 0.0))), 6),
    }
    if cell is not None:
        record["state"] = cell.state.name
        record["xp"] = int(cell.xp)
    record.update(payload)
    item.setdefault("fate_events", []).append(record)


def _candidate_child_pool(ctx: Mapping[str, Any], *, trigger: str) -> tuple[str, ...]:
    top = ctx["top_option"]
    second = ctx["second_option"]
    if trigger == "low_margin_action_ranking" and second is not None:
        return _generic_child_pool(set(top["active_keys"]) ^ set(second["active_keys"]))
    if trigger == "conflicting_active_atoms":
        return _generic_child_pool(top["positive_keys"] + top["negative_keys"] + top["active_keys"])
    return _generic_child_pool(top["active_keys"])


def _generic_child_pool(keys: Iterable[str]) -> tuple[str, ...]:
    scored: list[tuple[int, str]] = []
    for key in set(map(str, keys)):
        if _is_exact_coordinate_context_key(key):
            continue
        if key.startswith("action_pattern:"):
            score = 4
        elif key.startswith("delta_terminal:"):
            score = 3
        elif key.startswith("after_terminal:"):
            score = 2
        else:
            score = 1
        if _is_generic_context_key(key):
            score += 2
        scored.append((score, key))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return tuple(key for _score, key in scored)


def _choose_ecological_move(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    population: Mapping[str, Mapping[str, Any]],
    base_move_scores: Mapping[str, float] | None = None,
    seed: int,
    disabled_composite_ids: set[str],
    row_id: int | None = None,
    ply: int | None = None,
    segment_name: str | None = None,
    spawn_hook: Callable[[Mapping[str, Any]], None] | None = None,
) -> chess.Move | None:
    options = _score_options(
        board,
        counts,
        atom_weights=atom_weights,
        base_move_scores=base_move_scores,
        composites=population.values(),
        disabled_composite_ids=disabled_composite_ids,
        cfg=cfg,
    )
    if not options:
        return None
    if spawn_hook is not None:
        ctx = _decision_context(
            cfg,
            board,
            counts,
            options,
            seed=seed,
            row_id=row_id,
            ply=ply,
            segment_name=segment_name,
        )
        spawn_hook(ctx)
        options = _score_options(
            board,
            counts,
            atom_weights=atom_weights,
            base_move_scores=base_move_scores,
            composites=population.values(),
            disabled_composite_ids=disabled_composite_ids,
            cfg=cfg,
        )
    rng = random.Random(seed)
    rows = [(float(item["score"]), rng.random(), str(item["move"]), item["move"]) for item in options]
    rows.sort(reverse=True)
    return rows[0][-1]


def _choose_atom_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    seed: int,
) -> chess.Move | None:
    options = _score_options(
        board,
        counts,
        atom_weights=atom_weights,
        composites=(),
        disabled_composite_ids=set(),
    )
    if not options:
        return None
    rng = random.Random(seed)
    rows = [(float(item["atom_score"]), rng.random(), str(item["move"]), item["move"]) for item in options]
    rows.sort(reverse=True)
    return rows[0][-1]


def _choose_base_score_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    score_provider: Any,
    seed: int,
) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    if not legal:
        return None
    scores = _call_base_score_provider(score_provider, board, counts)
    rng = random.Random(seed)
    rows = [
        (float(scores.get(move.uci(), 0.0)), rng.random(), move.uci(), move)
        for move in legal
    ]
    rows.sort(reverse=True)
    return rows[0][-1]


def _call_base_score_provider(provider: Any, board: chess.Board, counts: Mapping[Any, int]) -> Mapping[str, float] | None:
    if provider is None:
        return None
    return provider(board, counts)


def _score_options(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    atom_weights: Mapping[str, float],
    base_move_scores: Mapping[str, float] | None = None,
    composites: Iterable[Mapping[str, Any]],
    disabled_composite_ids: set[str],
    cfg: StageBEcologicalDiscoveryConfig | None = None,
) -> list[dict[str, Any]]:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    live_composites = [
        item for item in composites
        if item.get("state", "TRIAL") in {"TRIAL", "MATURE"}
        and str(item["composite_id"]) not in disabled_composite_ids
    ]
    parent_local = bool(cfg is not None and cfg.ecology_mode == "stem_cell_graph")
    by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    if parent_local:
        for item in live_composites:
            by_parent[str(item.get("source_signature", ""))].append(item)
    options: list[dict[str, Any]] = []
    for move in legal:
        active_scales = _sealed_action_key_scales(board, move)
        active = {key for key, _scale in active_scales}
        option_composites = (
            by_parent.get(_percept_signature(active), ())
            if parent_local
            else live_composites
        )
        if base_move_scores is None:
            pos = sum(max(0.0, atom_weights.get(key, 0.0) * scale) for key, scale in active_scales)
            neg = sum(min(0.0, atom_weights.get(key, 0.0) * scale) for key, scale in active_scales)
            atom_score = pos + neg
        else:
            atom_score = float(base_move_scores.get(move.uci(), 0.0))
            pos = max(0.0, atom_score)
            neg = min(0.0, atom_score)
        active_composites = []
        composite_score = 0.0
        for comp in option_composites:
            children = tuple(map(str, comp["children"]))
            if all(child in active for child in children):
                active_composites.append(str(comp["composite_id"]))
                composite_score += _composite_weight(comp)
        options.append(
            {
                "move": move,
                "active_keys": tuple(sorted(active)),
                "active_composite_ids": tuple(sorted(active_composites)),
                "atom_score": atom_score,
                "positive_score": pos,
                "negative_score": neg,
                "positive_keys": tuple(key for key, scale in active_scales if atom_weights.get(key, 0.0) * scale > 0),
                "negative_keys": tuple(key for key, scale in active_scales if atom_weights.get(key, 0.0) * scale < 0),
                "composite_score": composite_score,
                "score": atom_score + composite_score,
            }
        )
    return options


def _decision_context(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    options: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    row_id: int | None,
    ply: int | None,
    segment_name: str | None = None,
) -> dict[str, Any]:
    del cfg
    ordered = sorted(options, key=lambda item: (float(item["atom_score"]), str(item["move"])), reverse=True)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else None
    margin = float(top["atom_score"]) - (float(second["atom_score"]) if second is not None else 0.0)
    return {
        "board_fen": board.fen(),
        "row_id": int(row_id) if row_id is not None else _stable_seed(board.fen()) % 10_000_000,
        "step": int(ply) if ply is not None else seed % 10_000_000,
        "segment": segment_name,
        "counts": dict(counts),
        "options": tuple(options),
        "top_option": top,
        "second_option": second,
        "margin": margin,
        "percept_signature": _percept_signature(top["active_keys"]),
    }


def _rollout_policy(
    cfg: StageBEcologicalDiscoveryConfig,
    row: Mapping[str, Any],
    chooser: Callable[[chess.Board, Mapping[Any, int], int, int, random.Random], chess.Move | None],
    *,
    seed: int,
    policy_name: str | None = None,
    collect_composites: bool = False,
    population: Mapping[str, Mapping[str, Any]] | None = None,
    judge_cache: _JudgeCache | None = None,
    success_kind: str = "stage_b_enter_mate2",
) -> dict[str, Any]:
    scorer = None if cfg.fast_exact_judge or success_kind == "approach_waypoint" else load_canonical_mate2_first_scorer()
    mate2_cache, enter_cache = judge_cache if judge_cache is not None else _new_judge_cache()
    board = chess.Board(str(row["fen"]))
    rng = random.Random(seed)
    counts: Counter[Any] = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
    white_steps: list[dict[str, str]] = []
    active_composite_ids: set[str] = set()
    percept_signatures: list[str] = []
    endpoint = "horizon"
    success = False
    for ply in range(cfg.horizon_plies):
        success_now, success_endpoint = _rollout_success_check(
            cfg,
            board,
            success_kind=success_kind,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        if success_now:
            endpoint = success_endpoint
            success = True
            break
        if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = chooser(board, counts, int(row["row_id"]), ply, rng)
        if move is None or move not in board.legal_moves:
            endpoint = "illegal"
            break
        if int(counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
            endpoint = "third_repetition"
            break
        if collect_composites and population:
            active = set(_sealed_action_keys(board, move))
            active_signature = _percept_signature(active)
            percept_signatures.append(active_signature)
            for comp in population.values():
                if comp.get("state") not in {"TRIAL", "MATURE"}:
                    continue
                if (
                    cfg.ecology_mode == "stem_cell_graph"
                    and str(comp.get("source_signature", "")) != active_signature
                ):
                    continue
                if all(str(child) in active for child in comp["children"]):
                    active_composite_ids.add(str(comp["composite_id"]))
        white_steps.append({"fen": board.fen(), "move": move.uci()})
        board.push(move)
        counts[_position_repetition_key(board)] += 1
        counts[board._transposition_key()] += 1
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if board.is_checkmate():
            endpoint = "mate_delivered"
            success = True
            break
        reply = _edge_mate_fixed_seed_black_reply(board, rng)
        if reply is None:
            endpoint = "mate_delivered" if board.is_check() else "stalemate"
            success = board.is_check()
            break
        board.push(reply)
        counts[_position_repetition_key(board)] += 1
        counts[board._transposition_key()] += 1
        if _white_rook_square(board) is None:
            endpoint = "rook_lost"
            break
        if board.is_stalemate():
            endpoint = "stalemate"
            break
        if not fence_established_geometry(board):
            endpoint = "fence_broken"
            break
    if not success and success_kind == "approach_waypoint" and _approach_waypoint_success(board):
        endpoint = "waypoint_reached"
        success = True
    reward = 6.0 if success else -6.0 if endpoint in {"fence_broken", "rook_lost", "stalemate", "illegal"} else -1.0
    return {
        "policy": policy_name,
        "row_id": int(row["row_id"]),
        "success": success,
        "endpoint": endpoint,
        "reward": reward,
        "plies": len(white_steps) * 2,
        "white_steps": white_steps,
        "active_composite_ids": sorted(active_composite_ids),
        "percept_signatures": percept_signatures,
    }


def _rollout_success_check(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    *,
    success_kind: str,
    scorer: Any,
    mate2_cache: dict[str, dict[str, Any]],
    enter_cache: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    if success_kind == "approach_waypoint":
        return (
            _approach_waypoint_success(board),
            "waypoint_reached",
        )
    if cfg.fast_exact_judge:
        audit = _fast_enter_mate2_audit(board)
    else:
        audit = _edge_mate_enter_mate2_audit(
            board,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
    return (
        bool(audit["confirmed"]),
        "ungated_exact_mate3_or_better_confirmed",
    )


def _approach_waypoint_success(board: chess.Board) -> bool:
    return bool(_king_support_waypoint_geometry(board) and fence_established_geometry(board))


def _evaluate_policy(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    chooser: Callable[[chess.Board, Mapping[Any, int], int, int, random.Random], chess.Move | None],
    *,
    seed: int,
    policy_name: str,
    judge_cache: _JudgeCache | None = None,
    collect_composites: bool = False,
    population: Mapping[str, Mapping[str, Any]] | None = None,
    success_kind: str = "stage_b_enter_mate2",
) -> dict[str, Any]:
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    samples: list[dict[str, Any]] = []
    plies_to_success: list[int] = []
    active_composite_ids: set[str] = set()
    active_composite_ids_by_row: dict[str, list[str]] = {}
    active_judge_cache = judge_cache if judge_cache is not None else _new_judge_cache()
    for index, row in enumerate(rows):
        outcome = _rollout_policy(
            cfg,
            row,
            chooser,
            seed=seed + index * 31,
            policy_name=policy_name,
            judge_cache=active_judge_cache,
            collect_composites=collect_composites,
            population=population,
            success_kind=success_kind,
        )
        row_active_ids = sorted(map(str, outcome.get("active_composite_ids", ())))
        active_composite_ids.update(row_active_ids)
        active_composite_ids_by_row[str(row["row_id"])] = row_active_ids
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoints[str(outcome["endpoint"])] += 1
        if outcome["success"]:
            plies_to_success.append(int(outcome["plies"]))
        elif len(samples) < cfg.max_samples:
            samples.append(
                {
                    "fen": row["fen"],
                    "endpoint": outcome["endpoint"],
                    "white_steps": outcome["white_steps"],
                }
            )
    wins = sum(int(value) for value in success_by_row.values())
    total = len(rows)
    return {
        "policy": policy_name,
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "active_composite_ids": sorted(active_composite_ids),
        "active_composite_ids_by_row": active_composite_ids_by_row,
        "mean_plies_to_success": None if not plies_to_success else sum(plies_to_success) / len(plies_to_success),
        "sample_nonwins": samples,
    }


def _apply_contrastive_nutrition(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    *,
    selected: Mapping[str, Any],
    alternative: Mapping[str, Any],
    step: int,
) -> None:
    selected_ids = set(map(str, selected["active_composite_ids"]))
    alternative_ids = set(map(str, alternative["active_composite_ids"]))
    exposed_signatures = set(map(str, selected.get("percept_signatures", ()))) | set(
        map(str, alternative.get("percept_signatures", ()))
    )
    reward_delta = float(selected["reward"]) - float(alternative["reward"])
    for comp in population.values():
        if comp["state"] not in {"TRIAL", "MATURE"}:
            continue
        cid = str(comp["composite_id"])
        habitat_exposed = str(comp.get("source_signature", "")) in exposed_signatures
        active = cid in selected_ids or cid in alternative_ids
        if cfg.ecology_mode != "habitat_local" or habitat_exposed or active:
            comp["nutrition"] = float(comp["nutrition"]) - cfg.passive_decay
            comp["passive_decay_events"] = int(comp["passive_decay_events"]) + 1
        if cid in selected_ids:
            comp["activation_count"] = int(comp["activation_count"]) + 1
            if reward_delta > 0:
                comp["nutrition"] = float(comp["nutrition"]) + cfg.positive_credit
                comp["credit_events"] = int(comp["credit_events"]) + 1
            elif reward_delta < 0:
                comp["nutrition"] = float(comp["nutrition"]) - cfg.negative_debt
                comp["debt_events"] = int(comp["debt_events"]) + 1
        if cid in alternative_ids and reward_delta > 0:
            comp["nutrition"] = float(comp["nutrition"]) - cfg.negative_debt
            comp["debt_events"] = int(comp["debt_events"]) + 1
        if float(comp["nutrition"]) >= cfg.mature_nutrition:
            comp["state"] = "MATURE"
        if float(comp["nutrition"]) <= 0.0:
            comp["state"] = "PRUNED"
            comp["prune_reason"] = "nutrition_depleted"
            comp["pruned_step"] = step
        else:
            comp["weight"] = _composite_weight(comp, cfg=cfg)


def _apply_stem_cell_local_economy(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    stem_cells: dict[str, StemCellTerminal],
    *,
    selected: Mapping[str, Any],
    alternative: Mapping[str, Any],
    step: int,
) -> None:
    selected_ids = set(map(str, selected["active_composite_ids"]))
    alternative_ids = set(map(str, alternative["active_composite_ids"]))
    exposed_signatures = set(map(str, selected.get("percept_signatures", ()))) | set(
        map(str, alternative.get("percept_signatures", ()))
    )
    reward_delta = float(selected["reward"]) - float(alternative["reward"])
    evidence: Counter[str] = Counter()
    if reward_delta > 0:
        evidence.update({cid: 1 for cid in selected_ids})
        evidence.update({cid: -1 for cid in alternative_ids})
    elif reward_delta < 0:
        evidence.update({cid: -1 for cid in selected_ids})
        evidence.update({cid: 1 for cid in alternative_ids})
    else:
        evidence.update({cid: 0 for cid in selected_ids | alternative_ids})

    exposed_parent_ids = {_stem_parent_id(signature) for signature in exposed_signatures}
    for cid, comp in population.items():
        if comp["state"] not in {"TRIAL", "MATURE"}:
            continue
        cell = stem_cells.get(cid)
        if cell is None:
            continue
        parent_id = str(comp.get("parent_id", ""))
        parent_exposed = parent_id in exposed_parent_ids
        active = cid in selected_ids or cid in alternative_ids
        if not parent_exposed and not active:
            if cell.state == StemCellState.TRIAL:
                comp["local_resource"] = (
                    float(comp.get("local_resource", comp.get("nutrition", 0.0)))
                    - cfg.passive_decay * cfg.stem_inactive_decay_scale
                )
                comp["nutrition"] = float(comp["local_resource"])
                comp["passive_decay_events"] = int(comp.get("passive_decay_events", 0)) + 1
                if float(comp.get("local_resource", 0.0)) <= 0.0:
                    cell.state = StemCellState.PRUNED
                    comp["state"] = "PRUNED"
                    comp["prune_reason"] = "local_inactive_decay_depleted"
                    comp["pruned_step"] = step
                    _record_fate_event(
                        comp,
                        step=step,
                        event="prune",
                        cell=cell,
                        reason="local_inactive_decay_depleted",
                    )
                comp["weight"] = _composite_weight(comp, cfg=cfg)
                _sync_stem_cell_record(comp, cell)
            continue

        if parent_exposed:
            cell.record_candidate_request(parent_id=parent_id)
            comp["exposure_count"] = int(comp.get("exposure_count", 0)) + 1
            comp["local_resource"] = float(comp.get("local_resource", comp.get("nutrition", 0.0))) - cfg.passive_decay
            comp["nutrition"] = float(comp["local_resource"])
            comp["passive_decay_events"] = int(comp.get("passive_decay_events", 0)) + 1
            cell.decay_xp()
            _record_fate_event(
                comp,
                step=step,
                event="exposure",
                cell=cell,
                parent_id=parent_id,
            )

        if active:
            cell.record_candidate_activation(parent_id=parent_id)
            comp["activation_count"] = int(comp.get("activation_count", 0)) + 1
            direction = int(evidence.get(cid, 0))
            if direction > 0:
                cell.update_xp(1.0)
                cell.mark_confirmed(step)
                comp["local_resource"] = float(comp.get("local_resource", comp.get("nutrition", 0.0))) + cfg.positive_credit
                comp["credit_events"] = int(comp.get("credit_events", 0)) + 1
                event = "local_credit"
            elif direction < 0:
                cell.update_xp(-1.0)
                comp["local_resource"] = float(comp.get("local_resource", comp.get("nutrition", 0.0))) - cfg.negative_debt
                comp["debt_events"] = int(comp.get("debt_events", 0)) + 1
                event = "local_debt"
            else:
                cell.record_candidate_intervention("neutral", cycle=step)
                comp["neutral_events"] = int(comp.get("neutral_events", 0)) + 1
                event = "local_neutral"
            comp["nutrition"] = float(comp["local_resource"])
            _record_fate_event(
                comp,
                step=step,
                event=event,
                cell=cell,
                reward_delta=round(reward_delta, 6),
            )

        if (
            cell.state == StemCellState.TRIAL
            and int(cell.xp) >= cfg.stem_mature_xp
            and int(comp.get("exposure_count", 0)) >= cfg.stem_min_mature_exposures
            and cell.candidate_can_mature()
        ):
            cell.state = StemCellState.MATURE
            comp["state"] = "MATURE"
            comp["mature_step"] = step
            _record_fate_event(comp, step=step, event="mature", cell=cell)

        if cell.state != StemCellState.MATURE and (
            float(comp.get("local_resource", 0.0)) <= 0.0 or int(cell.xp) <= cfg.stem_prune_xp
        ):
            cell.state = StemCellState.PRUNED
            comp["state"] = "PRUNED"
            comp["prune_reason"] = (
                "local_resource_depleted"
                if float(comp.get("local_resource", 0.0)) <= 0.0
                else "stem_xp_depleted"
            )
            comp["pruned_step"] = step
            _record_fate_event(comp, step=step, event="prune", cell=cell, reason=comp["prune_reason"])

        comp["weight"] = _composite_weight(comp, cfg=cfg)
        _sync_stem_cell_record(comp, cell)

    _record_exposed_sibling_ranks(population, step=step, parent_ids=exposed_parent_ids)


def _cap_population(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    *,
    step: int,
) -> None:
    live_trial = [item for item in population.values() if item["state"] == "TRIAL"]
    if cfg.ecology_mode == "global":
        _prune_lowest_nutrition(
            live_trial,
            overflow=len(live_trial) - cfg.max_population,
            step=step,
            reason="immature_population_cap",
        )
        return

    live_items = [
        item for item in population.values()
        if item["state"] in {"TRIAL", "MATURE"}
    ]
    by_habitat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in live_items:
        by_habitat[str(item.get("source_signature", ""))].append(item)
    for habitat_items in by_habitat.values():
        _prune_lowest_nutrition(
            habitat_items,
            overflow=len(habitat_items) - cfg.max_population_per_habitat,
            step=step,
            reason="habitat_population_cap",
        )
    total_limit = cfg.max_total_population or cfg.max_population
    remaining_live = [
        item for item in population.values()
        if item["state"] in {"TRIAL", "MATURE"}
    ]
    _prune_lowest_nutrition(
        remaining_live,
        overflow=len(remaining_live) - total_limit,
        step=step,
        reason="total_population_cap",
    )


def _cap_stem_cell_parent_budgets(
    cfg: StageBEcologicalDiscoveryConfig,
    population: dict[str, dict[str, Any]],
    stem_cells: dict[str, StemCellTerminal],
    *,
    step: int,
) -> None:
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in population.values():
        if item["state"] in {"TRIAL", "MATURE"}:
            by_parent[str(item.get("parent_id", ""))].append(item)

    for parent_id, siblings in by_parent.items():
        overflow = len(siblings) - cfg.max_population_per_habitat
        if overflow <= 0:
            continue
        siblings.sort(
            key=lambda item: (
                1 if item["state"] == "MATURE" else 0,
                float(item.get("local_resource", item.get("nutrition", 0.0))),
                int(item.get("stem_cell_xp") or 0),
                -int(item.get("birth_step", 0)),
                str(item["composite_id"]),
            )
        )
        for item in siblings[:overflow]:
            cid = str(item["composite_id"])
            cell = stem_cells.get(cid)
            if cell is not None:
                cell.state = StemCellState.PRUNED
            item["state"] = "PRUNED"
            item["prune_reason"] = "parent_local_resource_budget"
            item["pruned_step"] = step
            if cell is not None:
                _sync_stem_cell_record(item, cell)
            _record_fate_event(
                item,
                step=step,
                event="prune",
                cell=cell,
                reason="parent_local_resource_budget",
                parent_id=parent_id,
            )


def _record_exposed_sibling_ranks(
    population: Mapping[str, dict[str, Any]],
    *,
    step: int,
    parent_ids: set[str],
) -> None:
    if not parent_ids:
        return
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in population.values():
        if item["state"] in {"TRIAL", "MATURE"} and str(item.get("parent_id", "")) in parent_ids:
            by_parent[str(item.get("parent_id", ""))].append(item)
    for parent_id, siblings in by_parent.items():
        siblings.sort(
            key=lambda item: (
                item["state"] == "MATURE",
                float(item.get("local_resource", item.get("nutrition", 0.0))),
                int(item.get("stem_cell_xp") or 0),
                str(item["composite_id"]),
            ),
            reverse=True,
        )
        for rank, item in enumerate(siblings, start=1):
            history = item.setdefault("sibling_rank_history", [])
            if history and history[-1].get("rank") == rank and int(history[-1].get("step", -1)) == step:
                continue
            history.append(
                {
                    "step": int(step),
                    "parent_id": parent_id,
                    "rank": rank,
                    "sibling_count": len(siblings),
                    "local_resource": round(float(item.get("local_resource", 0.0)), 6),
                    "xp": item.get("stem_cell_xp"),
                }
            )


def _prune_lowest_nutrition(
    items: Sequence[dict[str, Any]],
    *,
    overflow: int,
    step: int,
    reason: str,
) -> None:
    if overflow <= 0:
        return
    ordered = list(items)
    ordered.sort(key=lambda item: (float(item["nutrition"]), int(item["birth_step"]), item["composite_id"]))
    for item in ordered[:overflow]:
        item["state"] = "PRUNED"
        item["prune_reason"] = reason
        item["pruned_step"] = step


def _composite_ablation_health(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    base_score_provider: Any | None = None,
    composites: Sequence[Mapping[str, Any]],
    seed: int,
    policy_name: str,
) -> dict[str, Any]:
    population = {str(item["composite_id"]): dict(item) for item in composites}
    judge_cache = _new_judge_cache()
    full_eval = _evaluate_policy(
        cfg,
        rows,
        lambda board, counts, row_id, ply, rng: _choose_ecological_move(
            cfg,
            board,
            counts,
            atom_weights=atom_weights,
            population=population,
            base_move_scores=_call_base_score_provider(base_score_provider, board, counts),
            seed=seed + int(row_id) * 47 + ply,
            disabled_composite_ids=set(),
            row_id=row_id,
            ply=ply,
        ),
        seed=seed,
        policy_name=policy_name,
        judge_cache=judge_cache,
        collect_composites=True,
        population=population,
    )
    active_on_full = set(map(str, full_eval.get("active_composite_ids", ())))
    active_by_row = {
        str(row_id): set(map(str, ids))
        for row_id, ids in full_eval.get("active_composite_ids_by_row", {}).items()
    }
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for comp in composites:
        cid = str(comp["composite_id"])
        if cid in active_on_full:
            active_rows = [
                row for row in rows
                if cid in active_by_row.get(str(row["row_id"]), set())
            ]
            full_active_wins = sum(
                int(bool(full_eval["success_by_row"].get(str(row["row_id"]), False)))
                for row in active_rows
            )
            ablated = _evaluate_policy(
                cfg,
                active_rows,
                lambda board, counts, row_id, ply, rng, cid=cid: _choose_ecological_move(
                    cfg,
                    board,
                    counts,
                    atom_weights=atom_weights,
                    population=population,
                    base_move_scores=_call_base_score_provider(base_score_provider, board, counts),
                    seed=seed + int(row_id) * 47 + ply,
                    disabled_composite_ids={cid},
                    row_id=row_id,
                    ply=ply,
                ),
                seed=seed,
                policy_name=f"{policy_name}_without_{cid}",
                judge_cache=judge_cache,
            )
            ablated_active_wins = int(ablated["wins"])
            ablated_wins = int(full_eval["wins"]) - full_active_wins + ablated_active_wins
            delta = full_active_wins - ablated_active_wins
        else:
            active_rows = []
            ablated_wins = int(full_eval["wins"])
            delta = 0
        classification = "load_bearing" if delta > 0 else "inert" if delta == 0 else "harmful"
        counts[classification] += 1
        records.append(
            {
                "composite_id": cid,
                "classification": classification,
                "full_wins": int(full_eval["wins"]),
                "ablated_wins": ablated_wins,
                "ablation_delta": delta,
                "active_on_full_heldout": cid in active_on_full,
                "active_row_count": len(active_rows),
                "birth_trigger": comp.get("birth_trigger"),
                "state": comp.get("state"),
                "nutrition": float(comp.get("nutrition", 0.0)),
                "children": list(comp.get("children", ())),
            }
        )
    return {
        "policy": policy_name,
        "composite_count": len(composites),
        "full_wins": int(full_eval["wins"]),
        "full_evaluation": full_eval,
        "load_bearing_count": int(counts["load_bearing"]),
        "inert_count": int(counts["inert"]),
        "harmful_count": int(counts["harmful"]),
        "nontrivial_delta_count": int(counts["load_bearing"] + counts["harmful"]),
        "records": records,
    }


def _pruned_rescue_audit(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    base_score_provider: Any | None = None,
    survivors: Sequence[Mapping[str, Any]],
    population: Mapping[str, Mapping[str, Any]],
    survivor_eval: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    pruned = [
        dict(item)
        for item in population.values()
        if item.get("state") == "PRUNED" and int(item.get("activation_count", 0)) > 0
    ]
    pruned.sort(
        key=lambda item: (
            -int(item.get("credit_events", 0)),
            -int(item.get("activation_count", 0)),
            int(item.get("pruned_step", 10**9)),
            str(item["composite_id"]),
        )
    )
    audited = pruned[: max(0, int(cfg.pruned_rescue_audit_limit))]
    audit_rows = list(rows[: max(0, int(cfg.pruned_rescue_heldout_limit))])
    survivor_population = {str(item["composite_id"]): dict(item) for item in survivors}
    records: list[dict[str, Any]] = []
    judge_cache = _new_judge_cache()
    baseline_screen_eval = _evaluate_policy(
        cfg,
        audit_rows,
        lambda board, counts, row_id, ply, rng, pop=survivor_population: _choose_ecological_move(
            cfg,
            board,
            counts,
            atom_weights=atom_weights,
            population=pop,
            base_move_scores=_call_base_score_provider(base_score_provider, board, counts),
            seed=seed + int(row_id) * 57 + ply,
            disabled_composite_ids=set(),
            row_id=row_id,
            ply=ply,
        ),
        seed=seed,
        policy_name="pruned_addback_screen_baseline",
        judge_cache=judge_cache,
    )
    baseline_screen_wins = int(baseline_screen_eval["wins"])
    for index, comp in enumerate(audited):
        rescued = dict(comp)
        rescued["state"] = "TRIAL"
        rescued["weight"] = max(float(rescued.get("weight", 0.0)), _composite_weight(rescued, cfg=cfg))
        rescue_population = {**survivor_population, str(rescued["composite_id"]): rescued}
        rescue_eval = _evaluate_policy(
            cfg,
            audit_rows,
            lambda board, counts, row_id, ply, rng, pop=rescue_population: _choose_ecological_move(
                cfg,
                board,
                counts,
                atom_weights=atom_weights,
                population=pop,
                base_move_scores=_call_base_score_provider(base_score_provider, board, counts),
                seed=seed + int(row_id) * 59 + ply,
                disabled_composite_ids=set(),
                row_id=row_id,
                ply=ply,
            ),
            seed=seed + index * 31,
            policy_name=f"pruned_addback_{rescued['composite_id']}",
            judge_cache=judge_cache,
        )
        delta = int(rescue_eval["wins"]) - baseline_screen_wins
        records.append(
            {
                "composite_id": str(rescued["composite_id"]),
                "children": list(rescued.get("children", ())),
                "birth_trigger": rescued.get("birth_trigger"),
                "birth_step": rescued.get("birth_step"),
                "pruned_step": rescued.get("pruned_step"),
                "prune_reason": rescued.get("prune_reason"),
                "training_credit_events": int(rescued.get("credit_events", 0)),
                "training_debt_events": int(rescued.get("debt_events", 0)),
                "training_activation_count": int(rescued.get("activation_count", 0)),
                "full_baseline_survivor_wins": int(survivor_eval["wins"]),
                "screen_baseline_survivor_wins": baseline_screen_wins,
                "addback_wins": int(rescue_eval["wins"]),
                "addback_delta": delta,
                "classification": "load_bearing_but_pruned" if delta > 0 else "inert_or_harmful_when_rescued",
            }
        )
    return {
        "enabled": True,
        "audit_method": "individual add-back of pruned candidates with training activation against final survivor policy",
        "audit_row_count": len(audit_rows),
        "full_heldout_row_count": int(survivor_eval["row_count"]),
        "candidate_pool_count": len(pruned),
        "audited_count": len(audited),
        "audit_limit": int(cfg.pruned_rescue_audit_limit),
        "load_bearing_but_pruned_count": sum(1 for record in records if int(record["addback_delta"]) > 0),
        "records": records,
    }


def _guided_residual_birth_plan(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    atom_weights: Mapping[str, float],
    *,
    seed: int,
    success_kind: str = "stage_b_enter_mate2",
) -> dict[int, list[dict[str, Any]]]:
    plan: dict[int, list[dict[str, Any]]] = defaultdict(list)
    budget = cfg.max_guided_births
    judge_cache = _new_judge_cache()
    for index, row in enumerate(rows):
        if budget <= 0:
            break
        atom_outcome = _rollout_policy(
            cfg,
            row,
            lambda board, counts, row_id, ply, rng: _choose_atom_move(
                board,
                counts,
                atom_weights=atom_weights,
                seed=seed + int(row_id) * 53 + ply,
            ),
            seed=seed + index * 17,
            judge_cache=judge_cache,
            success_kind=success_kind,
        )
        if atom_outcome["success"]:
            continue
        board = chess.Board(str(row["fen"]))
        options = _score_options(
            board,
            Counter({_position_repetition_key(board): 1, board._transposition_key(): 1}),
            atom_weights=atom_weights,
            composites=(),
            disabled_composite_ids=set(),
        )
        candidates: list[tuple[int, float, str, Mapping[str, Any]]] = []
        for option in options:
            forced = _rollout_forced_first_move(
                cfg,
                row,
                chess.Move.from_uci(str(option["move"])),
                atom_weights=atom_weights,
                seed=seed + index * 19,
                judge_cache=judge_cache,
                success_kind=success_kind,
            )
            candidates.append((int(forced["success"]), float(option["atom_score"]), str(option["move"]), option))
        candidates.sort(reverse=True)
        if not candidates or candidates[0][0] <= 0:
            continue
        option = candidates[0][-1]
        plan[int(row["row_id"])].append(
            {
                "target_move": str(option["move"]),
                "active_keys": _generic_child_pool(option["active_keys"]),
                "source_signature": _percept_signature(option["active_keys"]),
            }
        )
        budget -= 1
    return plan


def _rollout_forced_first_move(
    cfg: StageBEcologicalDiscoveryConfig,
    row: Mapping[str, Any],
    first_move: chess.Move,
    *,
    atom_weights: Mapping[str, float],
    seed: int,
    judge_cache: _JudgeCache | None = None,
    success_kind: str = "stage_b_enter_mate2",
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
        return _choose_atom_move(board, counts, atom_weights=atom_weights, seed=seed + row_id * 59 + ply)

    return _rollout_policy(cfg, row, chooser, seed=seed, judge_cache=judge_cache, success_kind=success_kind)


def _reference_baselines(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    scorer = load_canonical_mate2_first_scorer()
    gate = load_chain_confidence_gate()
    baseline_dir = Path(cfg.stage_b_baseline_dir)
    references: dict[str, Any] = {
        "fallback": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_fallback_move(board, counts, scorer=scorer),
            seed=20272900,
            policy_name="fallback_floor",
        ),
        "random": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_random_move(board, counts, rng=rng),
            seed=20272901,
            policy_name="random_floor",
        ),
        "dispatcher": _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng: _choose_dispatcher_move(
                board,
                counts,
                scorer=scorer,
                gate=gate,
            ),
            seed=20272902,
            policy_name="dispatcher_with_approach",
        ),
        "sealed_flat_weight_replay": {},
        "official_stage_b_flat": {},
    }
    for seed in cfg.flat_baseline_seeds:
        artifact_path = baseline_dir / f"stage_b_sealed_seed_{seed}.json"
        references["official_stage_b_flat"][str(seed)] = _load_official_flat_artifact(
            artifact_path,
            seed=seed,
        )
        weights = _load_weight_table(
            baseline_dir / f"stage_d_B_sealed_seed_{seed}_weights.json"
        )
        references["sealed_flat_weight_replay"][str(seed)] = _evaluate_policy(
            cfg,
            heldout_rows,
            lambda board, counts, row_id, ply, rng, weights=weights: _choose_atom_move(
                board,
                counts,
                atom_weights=weights,
                seed=seed + int(row_id) * 61 + ply,
            ),
            seed=seed + 700,
            policy_name=f"sealed_flat_weight_replay_{seed}",
        )
    return references


def _choose_fallback_move(board: chess.Board, counts: Mapping[Any, int], *, scorer) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    ordered = scorer.order_moves(board, legal)
    return ordered[0] if ordered else None


def _choose_random_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    rng: random.Random,
) -> chess.Move | None:
    legal = list(_legal_without_third_repetition(board, counts))
    if not legal:
        legal = sorted(board.legal_moves, key=lambda item: item.uci())
    return None if not legal else legal[rng.randrange(len(legal))]


def _choose_dispatcher_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    scorer,
    gate: Mapping[str, Any],
) -> chess.Move | None:
    result = run_krk_policy(
        board,
        gate=gate,
        scorer=scorer,
        record_trace=False,
        repetition_counts=counts,
        mate2_cache={},
        enter_cache={},
        enable_chase=True,
        enable_approach=True,
    )
    move = result.get("bound_move")
    if move is None:
        return _choose_fallback_move(board, counts, scorer=scorer)
    parsed = chess.Move.from_uci(str(move))
    return parsed if parsed in board.legal_moves else None


def _load_official_flat_artifact(path: Path, *, seed: int) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    heldout = payload["heldout_eval"]
    wins = int(heldout["success_count"])
    total = int(heldout["row_count"])
    return {
        "policy": f"official_stage_b_flat_{seed}",
        "artifact_path": str(path),
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson(wins, total),
        "endpoint_counts": dict(sorted(heldout["endpoint_counts"].items())),
        "success_by_row": {},
    }


def _load_weight_table(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = {
        str(item["terminal_key"]): float(item["local_weight"])
        for item in payload["weights"]
        if not learner_visible_key_firewall_leaks([str(item["terminal_key"])])
    }
    max_abs = max((abs(value) for value in raw.values()), default=1.0)
    if max_abs <= 0.0:
        max_abs = 1.0
    return {key: value / max_abs for key, value in raw.items()}


def _new_judge_cache() -> _JudgeCache:
    return ({}, {})


def _fast_enter_mate2_audit(board: chess.Board) -> dict[str, Any]:
    cache_key = _position_repetition_key(board)
    cached = _FAST_ENTER_MATE2_CACHE.get(cache_key)
    if cached is not None:
        return cached
    confirmed = _fast_enter_mate2_confirmed(board)
    audit = {
        "confirmed": confirmed,
        "frames": 0,
        "bound_move": None,
    }
    _FAST_ENTER_MATE2_CACHE[cache_key] = audit
    return audit


def _fast_enter_mate2_confirmed(board: chess.Board) -> bool:
    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        return False
    features = extract_learner_features(board)
    if (
        features["black_king_nearest_edge_distance"] != 0.0
        or not fence_established_geometry(board)
    ):
        return False
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after_white = _after_move(board, move)
        if _white_rook_square(after_white) is None:
            continue
        replies = tuple(sorted(after_white.legal_moves, key=lambda item: item.uci()))
        if not replies:
            if after_white.is_check():
                return True
            continue
        candidate_ok = True
        for reply in replies:
            successor = _after_move(after_white, reply)
            if (
                _white_rook_square(successor) is None
                or successor.is_stalemate()
                or not _fast_exact_mate2_confirmed(successor)
            ):
                candidate_ok = False
                break
        if candidate_ok:
            return True
    return False


def _fast_exact_mate2_confirmed(board: chess.Board) -> bool:
    cache_key = _position_repetition_key(board)
    cached = _FAST_EXACT_MATE2_CACHE.get(cache_key)
    if cached is not None:
        return cached
    confirmed = False
    if board.turn == chess.WHITE and not board.is_game_over(claim_draw=False) and not _fast_has_mate1(board):
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            after_first = _after_move(board, move)
            replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
            if replies and all(_fast_has_mate1(_after_move(after_first, reply)) for reply in replies):
                confirmed = True
                break
    _FAST_EXACT_MATE2_CACHE[cache_key] = confirmed
    return confirmed


def _fast_has_mate1(board: chess.Board) -> bool:
    cache_key = _position_repetition_key(board)
    cached = _FAST_MATE1_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        result = False
    else:
        result = False
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            after = _after_move(board, move)
            if after.is_checkmate():
                result = True
                break
    _FAST_MATE1_CACHE[cache_key] = result
    return result


def _after_move(board: chess.Board, move: chess.Move) -> chess.Board:
    after = board.copy(stack=False)
    after.push(move)
    return after


def _structure_summary(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    arm: str,
    seed: int,
    flat_seed: int,
    atom_weights: Mapping[str, float],
    population: Mapping[str, Mapping[str, Any]],
    survivors: Sequence[Mapping[str, Any]],
    trigger_counts: Mapping[str, int],
    guided_plan: Mapping[int, Sequence[Mapping[str, Any]]],
    processed_train_count: int,
    early_stop_reason: str | None,
) -> dict[str, Any]:
    all_children = sorted({child for comp in survivors for child in comp["children"]})
    counts = Counter(str(item["state"]) for item in population.values())
    live_parent_ids = {
        str(item.get("parent_id", ""))
        for item in population.values()
        if item["state"] in {"TRIAL", "MATURE"}
    }
    return {
        "schema_version": "phase2_9e_structure_summary.v0",
        "arm": arm,
        "seed": seed,
        "flat_baseline_seed": flat_seed,
        "processed_train_count": processed_train_count,
        "early_stop_reason": early_stop_reason,
        "atom_terminal_count": len(atom_weights),
        "birth_count": len(population),
        "survivor_count": len(survivors),
        "mature_count": int(counts["MATURE"]),
        "trial_count": int(counts["TRIAL"]),
        "pruned_count": int(counts["PRUNED"]),
        "cap_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "immature_population_cap"),
        "habitat_cap_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "habitat_population_cap"),
        "total_cap_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "total_population_cap"),
        "parent_budget_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "parent_local_resource_budget"),
        "local_resource_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "local_resource_depleted"),
        "inactive_decay_pruned_count": sum(1 for item in population.values() if item.get("prune_reason") == "local_inactive_decay_depleted"),
        "live_parent_count": len(live_parent_ids),
        "oracle_targeted_birth_count": sum(1 for item in population.values() if item.get("oracle_targeted_birth")),
        "trigger_distribution": dict(sorted(trigger_counts.items())),
        "error_set_targeted_birth_count": sum(len(items) for items in guided_plan.values()),
        "elsewhere_birth_count": len(population) - sum(1 for item in population.values() if item.get("oracle_targeted_birth")),
        "leak_count": sum(1 for key in all_children if learner_visible_key_firewall_leaks([key])),
        "node_count": 1 + len(all_children) + len(survivors),
        "edge_count": len(survivors) + sum(len(item["children"]) for item in survivors),
        "top_survivors": [
            {
                "composite_id": item["composite_id"],
                "state": item["state"],
                "birth_trigger": item["birth_trigger"],
                "birth_segment": item.get("birth_segment"),
                "nutrition": round(float(item["nutrition"]), 6),
                "local_resource": round(float(item.get("local_resource", item.get("nutrition", 0.0))), 6),
                "stem_cell_xp": item.get("stem_cell_xp"),
                "parent_id": item.get("parent_id"),
                "weight": round(_composite_weight(item), 6),
                "activation_count": int(item.get("activation_count", 0)),
                "exposure_count": int(item.get("exposure_count", 0)),
                "children": list(item["children"]),
            }
            for item in survivors[:16]
        ],
    }


def _population_snapshot(population: Mapping[str, Mapping[str, Any]], *, step: int) -> dict[str, Any]:
    counts = Counter(str(item["state"]) for item in population.values())
    alive_habitats = {
        str(item.get("source_signature", ""))
        for item in population.values()
        if item["state"] in {"TRIAL", "MATURE"}
    }
    mature_habitats = {
        str(item.get("source_signature", ""))
        for item in population.values()
        if item["state"] == "MATURE"
    }
    return {
        "step": step,
        "births_total": len(population),
        "alive_total": int(counts["TRIAL"] + counts["MATURE"]),
        "trial": int(counts["TRIAL"]),
        "mature": int(counts["MATURE"]),
        "pruned": int(counts["PRUNED"]),
        "alive_habitat_count": len(alive_habitats),
        "mature_habitat_count": len(mature_habitats),
    }


def _candidate_fate_log(population: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(population.values(), key=lambda row: (int(row.get("birth_step", 0)), str(row["composite_id"]))):
        rows.append(
            {
                "composite_id": str(item["composite_id"]),
                "children": list(item.get("children", ())),
                "birth_trigger": item.get("birth_trigger"),
                "birth_segment": item.get("birth_segment"),
                "birth_step": item.get("birth_step"),
                "birth_row_id": item.get("birth_row_id"),
                "parent_id": item.get("parent_id"),
                "source_signature": item.get("source_signature"),
                "state": item.get("state"),
                "mature_step": item.get("mature_step"),
                "pruned_step": item.get("pruned_step"),
                "prune_reason": item.get("prune_reason"),
                "stem_cell_id": item.get("stem_cell_id"),
                "stem_cell_xp": item.get("stem_cell_xp"),
                "local_resource": float(item.get("local_resource", item.get("nutrition", 0.0))),
                "exposure_count": int(item.get("exposure_count", 0)),
                "activation_count": int(item.get("activation_count", 0)),
                "credit_events": int(item.get("credit_events", 0)),
                "debt_events": int(item.get("debt_events", 0)),
                "neutral_events": int(item.get("neutral_events", 0)),
                "stem_cell_snapshot": item.get("stem_cell_snapshot"),
                "sibling_rank_history": list(item.get("sibling_rank_history", ())),
                "fate_events": list(item.get("fate_events", ())),
            }
        )
    return rows


def _survivor_failure_enrichment(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    base_score_provider: Any | None = None,
    composites: Sequence[Mapping[str, Any]],
    atom_eval: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    del cfg
    failure_rows = {int(row_id) for row_id, ok in atom_eval.get("success_by_row", {}).items() if not ok}
    success_rows = {int(row_id) for row_id, ok in atom_eval.get("success_by_row", {}).items() if ok}
    fire_failure = Counter()
    fire_success = Counter()
    by_id = {str(item["composite_id"]): item for item in composites}
    for row in heldout_rows:
        board = chess.Board(str(row["fen"]))
        counts = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
        move = (
            _choose_base_score_move(
                board,
                counts,
                score_provider=base_score_provider,
                seed=seed + int(row["row_id"]),
            )
            if base_score_provider is not None
            else _choose_atom_move(
                board,
                counts,
                atom_weights=atom_weights,
                seed=seed + int(row["row_id"]),
            )
        )
        if move is None:
            continue
        active = set(_sealed_action_keys(board, move))
        for cid, comp in by_id.items():
            if all(str(child) in active for child in comp["children"]):
                if int(row["row_id"]) in failure_rows:
                    fire_failure[cid] += 1
                elif int(row["row_id"]) in success_rows:
                    fire_success[cid] += 1
    return {
        "atom_failure_row_count": len(failure_rows),
        "atom_success_row_count": len(success_rows),
        "survivor_count": len(composites),
        "survivors_firing_on_atom_failure_count": sum(1 for cid in by_id if fire_failure[cid] > 0),
        "survivors_firing_on_atom_success_count": sum(1 for cid in by_id if fire_success[cid] > 0),
        "top_enriched": [
            {
                "composite_id": cid,
                "failure_fires": int(fire_failure[cid]),
                "success_fires": int(fire_success[cid]),
            }
            for cid in sorted(by_id, key=lambda item: (fire_failure[item], -fire_success[item], item), reverse=True)[:8]
        ],
    }


def _survivor_dumps(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    composites: Sequence[Mapping[str, Any]],
    health: Mapping[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    del seed
    by_health = {str(record["composite_id"]): record for record in health["records"]}
    dumps: list[dict[str, Any]] = []
    for comp in composites:
        cid = str(comp["composite_id"])
        record = by_health.get(cid, {})
        firing_cluster = _firing_cluster(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            comp=comp,
            limit=cfg.max_samples,
        )
        dumps.append(
            {
                "composite_id": cid,
                "classification": record.get("classification", "unclassified"),
                "ablation_delta": int(record.get("ablation_delta", 0)),
                "full_wins": int(record.get("full_wins", health.get("full_wins", 0))),
                "ablated_wins": int(record.get("ablated_wins", health.get("full_wins", 0))),
                "birth_trigger": comp.get("birth_trigger"),
                "birth_segment": comp.get("birth_segment"),
                "birth_row_id": comp.get("birth_row_id"),
                "state": comp.get("state"),
                "nutrition": float(comp.get("nutrition", 0.0)),
                "activation_count": int(comp.get("activation_count", 0)),
                "credit_events": int(comp.get("credit_events", 0)),
                "debt_events": int(comp.get("debt_events", 0)),
                "children": list(comp.get("children", ())),
                "normalized_children": _normalized_children(comp.get("children", ())),
                "firing_cluster": firing_cluster,
            }
        )
    return dumps


def _load_bearing_dumps(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    composites: Sequence[Mapping[str, Any]],
    health: Mapping[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    del seed
    by_id = {str(item["composite_id"]): item for item in composites}
    load_bearing = [
        record for record in health["records"]
        if record["classification"] == "load_bearing"
    ]
    dumps: list[dict[str, Any]] = []
    for record in load_bearing:
        comp = by_id[str(record["composite_id"])]
        firing_cluster = _firing_cluster(
            cfg,
            heldout_rows,
            atom_weights=atom_weights,
            comp=comp,
            limit=6,
        )
        dumps.append(
            {
                "composite_id": comp["composite_id"],
                "ablation_delta": int(record["ablation_delta"]),
                "birth_trigger": comp.get("birth_trigger"),
                "birth_segment": comp.get("birth_segment"),
                "children": list(comp["children"]),
                "firing_cluster": firing_cluster,
            }
        )
    return dumps


def _firing_cluster(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    comp: Mapping[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    firing_cluster = []
    for row in heldout_rows:
        board = chess.Board(str(row["fen"]))
        options = _score_options(
            board,
            Counter({_position_repetition_key(board): 1, board._transposition_key(): 1}),
            atom_weights=atom_weights,
            composites=[comp],
            disabled_composite_ids=set(),
            cfg=cfg,
        )
        fires = [
            str(option["move"])
            for option in options
            if str(comp["composite_id"]) in option["active_composite_ids"]
        ]
        if fires:
            firing_cluster.append(
                {
                    "row_id": int(row["row_id"]),
                    "fen": row["fen"],
                    "firing_moves": fires[:4],
                }
            )
        if len(firing_cluster) >= limit:
            break
    return firing_cluster


def _paired_yardstick_table(discovered: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    flat_seed, flat = max(
        references["sealed_flat_weight_replay"].items(),
        key=lambda item: int(item[1]["wins"]),
    )
    return {
        "random_floor": _paired_outcomes(discovered, references["random"]),
        "fallback_floor": _paired_outcomes(discovered, references["fallback"]),
        "dispatcher": _paired_outcomes(discovered, references["dispatcher"]),
        f"clean_flat_weight_replay_{flat_seed}": _paired_outcomes(discovered, flat),
    }


def _paired_outcomes(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
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
    return {
        "left_policy": left["policy"],
        "right_policy": right["policy"],
        "paired_row_count": len(common),
        "left_wins": int(left["wins"]),
        "right_wins": int(right["wins"]),
        "left_minus_right_wins": int(left["wins"]) - int(right["wins"]),
        "win_win": int(counts["win_win"]),
        "win_loss": int(counts["win_loss"]),
        "loss_win": int(counts["loss_win"]),
        "loss_loss": int(counts["loss_loss"]),
    }


def _summary_tables(seed_results: Mapping[str, Any], references: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for seed, result in seed_results.items():
        arm_names = [
            key for key, value in result.items()
            if isinstance(value, Mapping) and str(key).startswith("arm")
        ]
        for arm_name in arm_names:
            arm = result[arm_name]
            health = arm["post_hoc_ablation"]
            eval_row = arm["evaluations"]["survivor_trial"]
            rows.append(
                {
                    "seed": int(seed),
                    "arm": arm_name,
                    "wins": int(eval_row["wins"]),
                    "row_count": int(eval_row["row_count"]),
                    "win_rate": float(eval_row["win_rate"]),
                    "load_bearing": int(health["load_bearing_count"]),
                    "inert": int(health["inert_count"]),
                    "harmful": int(health["harmful_count"]),
                    "births": int(arm["structure"]["birth_count"]),
                    "survivors": int(arm["structure"]["survivor_count"]),
                    "mature": int(arm["structure"]["mature_count"]),
                    "pruned": int(arm["structure"]["pruned_count"]),
                }
            )
    yardsticks = {
        "random": _compact_eval(references["random"]),
        "fallback": _compact_eval(references["fallback"]),
        "dispatcher": _compact_eval(references["dispatcher"]),
        "flat_replays": {
            seed: _compact_eval(item)
            for seed, item in references["sealed_flat_weight_replay"].items()
        },
        "official_flat": {
            seed: _compact_eval(item)
            for seed, item in references["official_stage_b_flat"].items()
        },
    }
    if "native_foundation_base" in references:
        yardsticks["native_foundation_base"] = _compact_eval(references["native_foundation_base"])
    return {"arm_seed_table": rows, "yardsticks": yardsticks}


def _cross_seed_composite_analysis(seed_results: Mapping[str, Any]) -> dict[str, Any]:
    recurrence: dict[tuple[str, ...], dict[str, Any]] = {}
    for seed, result in seed_results.items():
        arm = result["arm1_unguided_ecological"]
        for dump in arm.get("survivor_composite_dumps", ()):
            key = tuple(dump["normalized_children"])
            row = recurrence.setdefault(
                key,
                {
                    "normalized_children": list(key),
                    "survivor_seed_count": 0,
                    "load_bearing_seed_count": 0,
                    "seeds": [],
                    "load_bearing_seeds": [],
                    "classifications": Counter(),
                    "ablation_deltas": [],
                    "birth_triggers": Counter(),
                },
            )
            row["survivor_seed_count"] += 1
            row["seeds"].append(int(seed))
            classification = str(dump.get("classification", "unclassified"))
            row["classifications"][classification] += 1
            row["ablation_deltas"].append(int(dump.get("ablation_delta", 0)))
            row["birth_triggers"][str(dump.get("birth_trigger", "unknown"))] += 1
            if classification == "load_bearing":
                row["load_bearing_seed_count"] += 1
                row["load_bearing_seeds"].append(int(seed))
    rows = []
    for row in recurrence.values():
        rows.append(
            {
                **{
                    key: value
                    for key, value in row.items()
                    if key not in {"classifications", "birth_triggers"}
                },
                "classifications": dict(sorted(row["classifications"].items())),
                "birth_triggers": dict(sorted(row["birth_triggers"].items())),
            }
        )
    rows.sort(
        key=lambda item: (
            int(item["load_bearing_seed_count"]),
            int(item["survivor_seed_count"]),
            sum(int(delta) for delta in item["ablation_deltas"]),
            item["normalized_children"],
        ),
        reverse=True,
    )
    return {
        "survivor_unique_composite_count": len(rows),
        "recurring_survivors": [row for row in rows if int(row["survivor_seed_count"]) > 1],
        "recurring_load_bearing": [row for row in rows if int(row["load_bearing_seed_count"]) > 1],
        "all_survivor_composites": rows,
    }


def _enrichment_summary(seed_results: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for seed, result in seed_results.items():
        enrichment = result["arm1_unguided_ecological"]["post_hoc_failure_enrichment"]
        rows.append(
            {
                "seed": int(seed),
                "atom_failure_row_count": int(enrichment["atom_failure_row_count"]),
                "atom_success_row_count": int(enrichment["atom_success_row_count"]),
                "survivor_count": int(enrichment["survivor_count"]),
                "survivors_firing_on_atom_failure_count": int(
                    enrichment["survivors_firing_on_atom_failure_count"]
                ),
                "survivors_firing_on_atom_success_count": int(
                    enrichment["survivors_firing_on_atom_success_count"]
                ),
                "top_enriched": enrichment["top_enriched"],
            }
        )
    return {"per_seed": rows}


def _phase29f_headline(summary: Mapping[str, Any]) -> dict[str, Any]:
    arm_rows = [
        row for row in summary["tables"]["arm_seed_table"]
        if row["arm"] == "arm1_unguided_ecological"
    ]
    return {
        "arm1_load_bearing_counts": [
            int(row["load_bearing"]) for row in arm_rows
        ],
        "arm1_wins": [int(row["wins"]) for row in arm_rows],
        "arm1_vs_dispatcher_81": [
            int(row["wins"]) - 81 for row in arm_rows
        ],
        "arm1_vs_official_flat_92": [
            int(row["wins"]) - 92 for row in arm_rows
        ],
        "recurring_load_bearing": summary["cross_seed_composite_analysis"]["recurring_load_bearing"],
    }


def _maturity_summary(seed_results: Mapping[str, Any]) -> dict[str, Any]:
    mature_recurrence: dict[tuple[str, ...], dict[str, Any]] = {}
    per_seed = []
    for seed, result in seed_results.items():
        arm = result["arm1_unguided_ecological"]
        mature_candidates = [
            row for row in arm.get("candidate_fate_log", ())
            if row.get("state") == "MATURE"
        ]
        per_seed.append(
            {
                "seed": int(seed),
                "mature_count": len(mature_candidates),
                "survivor_count": int(arm["structure"]["survivor_count"]),
                "live_parent_count": int(arm["structure"].get("live_parent_count", 0)),
                "load_bearing_count": int(arm["post_hoc_ablation"]["load_bearing_count"]),
                "load_bearing_but_pruned_count": int(
                    arm.get("pruned_rescue_audit", {}).get("load_bearing_but_pruned_count", 0)
                ),
                "birth_death_curve": arm.get("birth_death_curve", ()),
            }
        )
        for row in mature_candidates:
            key = tuple(_normalized_children(row.get("children", ())))
            item = mature_recurrence.setdefault(
                key,
                {
                    "normalized_children": list(key),
                    "mature_seed_count": 0,
                    "seeds": [],
                    "birth_triggers": Counter(),
                },
            )
            item["mature_seed_count"] += 1
            item["seeds"].append(int(seed))
            item["birth_triggers"][str(row.get("birth_trigger", "unknown"))] += 1
    recurrence_rows = [
        {
            "normalized_children": row["normalized_children"],
            "mature_seed_count": int(row["mature_seed_count"]),
            "seeds": row["seeds"],
            "birth_triggers": dict(sorted(row["birth_triggers"].items())),
        }
        for row in mature_recurrence.values()
    ]
    recurrence_rows.sort(key=lambda row: (int(row["mature_seed_count"]), row["normalized_children"]), reverse=True)
    return {
        "per_seed": per_seed,
        "recurring_mature_composites": [
            row for row in recurrence_rows if int(row["mature_seed_count"]) > 1
        ],
        "all_mature_composites": recurrence_rows,
    }


def _phase30_headline(summary: Mapping[str, Any]) -> dict[str, Any]:
    arm_rows = [
        row for row in summary["tables"]["arm_seed_table"]
        if row["arm"] == "arm1_unguided_ecological"
    ]
    maturity = summary.get("maturity_summary", {})
    per_seed = maturity.get("per_seed", ())
    return {
        "arm1_mature_counts": [int(row["mature"]) for row in arm_rows],
        "arm1_load_bearing_counts": [int(row["load_bearing"]) for row in arm_rows],
        "arm1_wins": [int(row["wins"]) for row in arm_rows],
        "recurring_mature_composites": maturity.get("recurring_mature_composites", []),
        "recurring_load_bearing": summary["cross_seed_composite_analysis"]["recurring_load_bearing"],
        "load_bearing_but_pruned_counts": [
            int(row.get("load_bearing_but_pruned_count", 0)) for row in per_seed
        ],
    }


def _phase31_headline(summary: Mapping[str, Any]) -> dict[str, Any]:
    base = _phase30_headline(summary)
    carryover_rows = []
    for seed, result in summary["seed_results"].items():
        arm = result["arm1_unguided_ecological"]
        carryover = arm["structure"].get("curriculum_carryover", {})
        carryover_rows.append(
            {
                "seed": int(seed),
                "births_by_segment": carryover.get("births_by_segment", {}),
                "survivors_by_birth_segment": carryover.get("survivors_by_birth_segment", {}),
                "segments": carryover.get("segments", []),
            }
        )
    base["carryover"] = {
        "same_population_across_stage_a_b": True,
        "full_foundation_curriculum": False,
        "per_seed": carryover_rows,
    }
    return base


def _phase32_headline(summary: Mapping[str, Any]) -> dict[str, Any]:
    base = _phase30_headline(summary)
    coverage = summary.get("native_foundation_coverage", {})
    native_eval = summary.get("reference_baselines", {}).get("native_foundation_base", {})
    base["native_foundation"] = {
        "key_mode": summary.get("native_foundation", {}).get("decision", {}).get("key_mode"),
        "foundation_checkpoint_pass": summary.get("native_foundation", {}).get("decision", {}).get("checkpoint_pass"),
        "base_wins": native_eval.get("wins"),
        "base_row_count": native_eval.get("row_count"),
        "coverage": coverage,
    }
    return base


def _seed_decision(arm1: Mapping[str, Any], arm2: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "arm1_load_bearing_gt_zero": int(arm1["post_hoc_ablation"]["load_bearing_count"]) > 0,
        "arm2_load_bearing_gt_zero": int(arm2["post_hoc_ablation"]["load_bearing_count"]) > 0,
        "arm1_population_collapse": bool(arm1["stop_rule"]["population_collapse_to_zero"]),
        "arm1_unbounded_explosion": bool(arm1["stop_rule"]["unbounded_explosion_cap_pressure"]),
    }


def _overall_decision(seed_results: Mapping[str, Any]) -> dict[str, Any]:
    arm1_load = [
        int(result["arm1_unguided_ecological"]["post_hoc_ablation"]["load_bearing_count"])
        for result in seed_results.values()
    ]
    arm2_load = [
        int(result.get("arm2_guided_residual_control", {}).get("post_hoc_ablation", {}).get("load_bearing_count", 0))
        for result in seed_results.values()
    ]
    arm1_wins = [
        int(result["arm1_unguided_ecological"]["evaluations"]["survivor_trial"]["wins"])
        for result in seed_results.values()
    ]
    collapse = any(
        bool(result["arm1_unguided_ecological"]["stop_rule"]["population_collapse_to_zero"])
        for result in seed_results.values()
    )
    explosion = any(
        bool(result["arm1_unguided_ecological"]["stop_rule"]["unbounded_explosion_cap_pressure"])
        for result in seed_results.values()
    )
    if any(count > 0 for count in arm1_load):
        interpretation = "arm1_discovery_positive_audit_survivors"
    elif any(count > 0 for count in arm2_load):
        interpretation = "substrate_can_express_useful_composite_ecology_too_weak"
    else:
        interpretation = "flat_substrate_did_not_host_load_bearing_composition_step5_required"
    return {
        "arm1_load_bearing_counts": arm1_load,
        "arm2_load_bearing_counts": arm2_load,
        "arm1_wins": arm1_wins,
        "arm1_seed_spread": 0 if not arm1_wins else max(arm1_wins) - min(arm1_wins),
        "population_collapse_stop": collapse,
        "unbounded_explosion_stop": explosion,
        "all_arm1_load_bearing_zero": all(count == 0 for count in arm1_load),
        "interpretation": interpretation,
    }


def _compact_eval(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "wins": int(item["wins"]),
        "nonwins": int(item["nonwins"]),
        "row_count": int(item["row_count"]),
        "win_rate": float(item["win_rate"]),
        "wilson_95": list(item["wilson_95"]),
        "endpoint_counts": dict(item["endpoint_counts"]),
    }


def _legal_without_third_repetition(board: chess.Board, counts: Mapping[Any, int]) -> tuple[chess.Move, ...]:
    return tuple(
        move
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
        if int(counts.get(_after_move_repetition_key(board, move), 0)) < 2
    )


def _sealed_action_keys(board: chess.Board, move: chess.Move) -> tuple[str, ...]:
    return tuple(key for key, _scale in _sealed_action_key_scales(board, move))


def _sealed_action_key_scales(board: chess.Board, move: chess.Move) -> tuple[tuple[str, float], ...]:
    cache_key = (board.fen(), move.uci())
    cached = _ACTION_KEY_SCALE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    pairs = tuple((key, float(scale)) for key, scale in terminal_action_feature_keys(board, move))
    keys = tuple(key for key, _scale in pairs)
    validate_learner_visible_keys(keys, builder="stage_b_ecological_discovery_probe._sealed_action_keys")
    _ACTION_KEY_SCALE_CACHE[cache_key] = pairs
    return pairs


def _composite_weight(
    comp: Mapping[str, Any],
    *,
    cfg: StageBEcologicalDiscoveryConfig | None = None,
) -> float:
    if cfg is None:
        return float(comp.get("weight", 0.0))
    nutrition = max(0.0, float(comp.get("nutrition", 0.0)))
    return min(cfg.max_advisory_weight, cfg.initial_weight + nutrition * cfg.nutrition_weight_scale)


def _composite_id(arm: str, children: Sequence[str]) -> str:
    digest = hashlib.sha256((arm + "\n" + "\n".join(children)).encode("utf-8")).hexdigest()
    prefix = "eco" if arm == "arm1_unguided_ecological" else "guided"
    return f"stage_b_{prefix}_quorum_{digest[:12]}"


def _normalized_children(children: Iterable[str]) -> list[str]:
    return sorted(map(str, children))


def _percept_signature(keys: Iterable[str]) -> str:
    before = [
        key for key in map(str, keys)
        if key.startswith("before_terminal:")
        and _is_generic_context_key(key)
        and not _is_exact_coordinate_context_key(key)
    ]
    if not before:
        before = [
            key for key in map(str, keys)
            if key.startswith("before_terminal:")
            and not _is_exact_coordinate_context_key(key)
        ]
    digest = hashlib.sha256("\n".join(sorted(set(before))[:16]).encode("utf-8")).hexdigest()
    return f"percept_{digest[:12]}"


def _is_generic_context_key(key: str) -> bool:
    fragments = (
        "neighbor",
        "corner_distance",
        "edge",
        "distance",
        "king_support",
        "rook_attacked",
        "rook_present",
        "same_side",
        "opposite_sides",
        "side_white_to_move",
        "is_check",
        "black_king",
        "white_king",
        "white_rook",
    )
    return any(fragment in key for fragment in fragments)


def _is_exact_coordinate_context_key(key: str) -> bool:
    name = key.split(":", 1)[-1].split("=", 1)[0]
    return name.endswith("_file") or name.endswith("_rank")


def _stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _wilson(success: int, total: int) -> list[float]:
    if total <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = success / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1.0 - p) / total + z * z / (4 * total * total)) / denom
    return [center - margin, center + margin]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
