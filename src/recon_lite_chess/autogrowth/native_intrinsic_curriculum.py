"""Native empty-learned-state KRK R0/R1 curriculum.

This runner joins the TG26p native graph substrate to the generic intrinsic
credit engine. Exact mate predicates are used only to construct trainer-side
curriculum pools. Training credit comes from an executed world transition or a
mature child's consolidated value; no correct-move set is passed to the learner.

The formal ReCoN engine confirms action branches. Weighted arbitration remains
the existing content-blind Python host operation and is reported as such.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import copy
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import pickle
import platform
import random
import resource
import subprocess
from time import perf_counter
from typing import Any, Callable, Iterable, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes.stem_cell import StemCellState

from recon_lite_hector.learning import (
    CompetenceGateExample,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedPrototypeGate,
    PrototypeCompetenceGateConfig,
    Responsibility,
)

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _random_krk_board,
    _valid_foundation_board,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    ROOT_ID,
)


R0_COMPETENCE_ID = "native_intrinsic_r0_mate_in_1"
R1_COMPETENCE_ID = "native_intrinsic_r1_mate_in_2"
V2_PROSPECTIVE_AVAILABILITY = "v2_prospective"
GATE_FEATURE_NAMES = (
    "selected_score",
    "selected_margin",
    "confirmed_candidate_count",
    "candidate_triplet_count",
    "top4_score_mean",
    "top4_score_std",
    "top16_score_mean",
    "top16_score_std",
    "top_score_range",
    "selected_score_squared",
    "selected_margin_squared",
    "score_margin_interaction",
    "distinct_top_move_count",
    "distinct_top_triplet_count",
)

R1_BALANCED_STRATA = (
    "rook_barrier:left",
    "rook_barrier:right",
    "rook_barrier:bottom",
    "rook_barrier:top",
    "king_edge:left",
    "king_edge:right",
    "king_edge:bottom",
    "king_edge:top",
    "king_corner:a1",
    "king_corner:a8",
    "king_corner:h1",
    "king_corner:h8",
)
R0_BALANCED_STRATA = (
    "black_king_edge:left",
    "black_king_edge:right",
    "black_king_edge:bottom",
    "black_king_edge:top",
    "black_king_corner:a1",
    "black_king_corner:a8",
    "black_king_corner:h1",
    "black_king_corner:h8",
)
R1_RETIRED_DEVELOPMENT_FENS = (
    "8/8/1R6/8/8/1K6/8/1k6 w - - 0 1",
    "R7/8/8/8/1K6/8/8/1k6 w - - 0 1",
    "8/8/7R/8/8/4K3/8/5k2 w - - 0 1",
    "8/3R4/8/8/8/2K5/8/k7 w - - 0 1",
    "8/8/8/8/8/3R3K/8/6k1 w - - 0 1",
    "8/8/5K2/7k/8/8/8/2R5 w - - 0 1",
    "5K2/7k/8/8/8/8/R7/8 w - - 0 1",
    "8/7k/5K2/8/8/8/R7/8 w - - 0 1",
    "2R5/8/8/8/8/5K2/7k/8 w - - 0 1",
    "8/8/8/8/4K3/7k/R7/8 w - - 0 1",
    "8/5K2/7k/8/8/8/8/1R6 w - - 0 1",
    "k7/8/2K5/7R/8/8/8/8 w - - 0 1",
    "2k5/8/8/2K5/8/8/8/1R6 w - - 0 1",
    "R7/8/8/8/8/2K5/8/1k6 w - - 0 1",
    "8/8/8/8/3R4/4K3/8/7k w - - 0 1",
    "k7/8/8/2K5/4R3/8/8/8 w - - 0 1",
)


@dataclass(frozen=True)
class NativeIntrinsicCurriculumConfig:
    output_path: str = (
        "reports/autogrowth/native_from_scratch/"
        "native_intrinsic_r0_r1_summary.json"
    )
    progress_path: str = (
        "reports/autogrowth/native_from_scratch/"
        "native_intrinsic_r0_r1_progress.json"
    )
    seed: int = 20260710
    max_generation_attempts: int = 500_000
    r0_train_count: int = 32
    r0_validation_count: int = 16
    r0_regression_count: int = 16
    r0_gate_train_decoy_count: int = 32
    r0_gate_validation_decoy_count: int = 16
    r0_gate_regression_decoy_count: int = 16
    r1_train_count: int = 24
    r1_validation_count: int = 12
    r1_regression_count: int = 12
    r0_pool_mode: str = "random"
    r0_excluded_fens: tuple[str, ...] = ()
    r1_pool_mode: str = "random"
    r0_epochs: int = 72
    r1_epochs: int = 120
    r0_replay_per_r1_epoch: int = 8
    r0_validation_interval: int = 4
    r1_validation_interval: int = 20
    r1_snapshot_interval: int = 20
    r1_snapshot_dir: str = "snapshots/autogrowth/native_intrinsic_r1"
    resume_r1_snapshots: bool = True
    r1_keep_checkpoint_history: bool = True
    r0_mastery_threshold: float = 1.0
    r1_mastery_threshold: float = 1.0
    run_r1: bool = True
    freeze_r0_parameters_for_r1: bool = True
    run_redundant_child_ablation: bool = False
    mature_child_priority: bool = True
    r0_availability_mode: str = "virtual_frame_verified"
    r1_mechanistic_factorial: bool = False
    r1_placebo_child_value: float = 0.5
    r1_shuffle_seed: int = 20260722
    r0_child_cache_validation_mode: str = "live_formal"
    r1_composite_proposal_epochs: tuple[int, ...] = ()
    r1_composite_consolidation_epochs: tuple[int, ...] = ()
    r1_composite_max_candidates: int = 8
    r1_composite_max_atoms_per_triplet: int = 64
    r1_composite_min_support: int = 2
    r1_heldout_mature_composites_only: bool = True
    development_wall_ceiling_seconds: float | None = None
    development_peak_rss_ceiling_mib: float | None = None
    development_fen_fullmove_base: int | None = None
    eta_m3: float = 0.08
    eta_fast: float = 0.20
    eta_slow: float = 1.0
    real_move_cost: float = 0.01
    min_grounding_evidence: int = 3
    max_ticks: int = 80
    max_samples: int = 12


@dataclass(frozen=True)
class R1MechanisticArm:
    """One causally named R1 mechanism configuration.

    Availability, emitted value, runtime routing, and structural growth are
    explicit factors. This prevents the historical ``full_intrinsic`` bundle
    from being interpreted as evidence for any one of its ingredients.
    """

    name: str
    bootstrap_enabled: bool
    availability_mode: str = "none"
    child_value_mode: str = "learned"
    mature_child_priority: bool = False
    hierarchy_edge_scoring: bool = True
    composition_enabled: bool = False

    def __post_init__(self) -> None:
        if self.availability_mode not in {
            "none",
            "prototype_gate",
            "virtual_frame_verified",
            "shuffled_prototype_gate",
            V2_PROSPECTIVE_AVAILABILITY,
        }:
            raise ValueError(f"unsupported R1 availability mode: {self.availability_mode}")
        if self.child_value_mode not in {"learned", "zero", "constant"}:
            raise ValueError(f"unsupported R1 child value mode: {self.child_value_mode}")
        if not self.bootstrap_enabled and self.availability_mode != "none":
            raise ValueError("disabled bootstrap requires availability_mode='none'")


def _legacy_r1_arm(name: str, config: NativeIntrinsicCurriculumConfig) -> R1MechanisticArm:
    bootstrap = name in {"full_intrinsic", "child_ablation"}
    return R1MechanisticArm(
        name=name,
        bootstrap_enabled=bootstrap,
        availability_mode=config.r0_availability_mode if bootstrap else "none",
        child_value_mode="learned",
        mature_child_priority=(
            config.mature_child_priority and name != "child_ablation"
        ),
        hierarchy_edge_scoring=True,
        composition_enabled=name == "full_intrinsic",
    )


def _mechanistic_r1_arms(config: NativeIntrinsicCurriculumConfig) -> tuple[R1MechanisticArm, ...]:
    """Return the development factorial; composition is intentionally absent."""

    return (
        R1MechanisticArm(
            name="no_bootstrap",
            bootstrap_enabled=False,
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="learned_gate_learned_value",
            bootstrap_enabled=True,
            availability_mode="prototype_gate",
            child_value_mode="learned",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="learned_gate_zero_value",
            bootstrap_enabled=True,
            availability_mode="prototype_gate",
            child_value_mode="zero",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="shuffled_gate_learned_value",
            bootstrap_enabled=True,
            availability_mode="shuffled_prototype_gate",
            child_value_mode="learned",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="exact_verify_learned_value",
            bootstrap_enabled=True,
            availability_mode="virtual_frame_verified",
            child_value_mode="learned",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="exact_verify_zero_value",
            bootstrap_enabled=True,
            availability_mode="virtual_frame_verified",
            child_value_mode="zero",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="exact_verify_constant_value",
            bootstrap_enabled=True,
            availability_mode="virtual_frame_verified",
            child_value_mode="constant",
            mature_child_priority=True,
        ),
        R1MechanisticArm(
            name="exact_verify_learned_value_no_hierarchy_score",
            bootstrap_enabled=True,
            availability_mode="virtual_frame_verified",
            child_value_mode="learned",
            mature_child_priority=True,
            hierarchy_edge_scoring=False,
        ),
    )


def _apply_child_value_control(
    credit: IntrinsicCreditEngine,
    arm: R1MechanisticArm,
    config: NativeIntrinsicCurriculumConfig,
) -> dict[str, Any]:
    state = credit.states[R0_COMPETENCE_ID]
    learned_value = float(state.slow_value)
    if arm.child_value_mode == "zero":
        state.slow_value = 0.0
    elif arm.child_value_mode == "constant":
        state.slow_value = float(config.r1_placebo_child_value)
    return {
        "mode": arm.child_value_mode,
        "learned_value_before_control": learned_value,
        "emitted_value_after_control": float(state.slow_value),
    }


@dataclass(frozen=True)
class NativeIntrinsicCurriculumResult:
    config: NativeIntrinsicCurriculumConfig
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_native_intrinsic_r0_r1.v0",
            "checkpoint": "native_from_scratch_r0_r1",
            "config": asdict(self.config),
            **self.payload,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return output


@dataclass(frozen=True)
class _Pools:
    r0_train: tuple[str, ...]
    r0_validation: tuple[str, ...]
    r0_regression: tuple[str, ...]
    gate_train_decoys: tuple[str, ...]
    gate_validation_decoys: tuple[str, ...]
    gate_regression_decoys: tuple[str, ...]
    r1_train: tuple[str, ...]
    r1_validation: tuple[str, ...]
    r1_regression: tuple[str, ...]
    r0_train_strata: tuple[str, ...]
    r0_validation_strata: tuple[str, ...]
    r0_regression_strata: tuple[str, ...]
    r0_excluded_fens: tuple[str, ...]
    r0_pool_mode: str
    r1_train_strata: tuple[str, ...]
    r1_validation_strata: tuple[str, ...]
    r1_regression_strata: tuple[str, ...]
    r1_pool_mode: str

    def manifest(self) -> dict[str, Any]:
        groups = {
            "r0_train": self.r0_train,
            "r0_validation": self.r0_validation,
            "r0_regression": self.r0_regression,
            "gate_train_decoys": self.gate_train_decoys,
            "gate_validation_decoys": self.gate_validation_decoys,
            "gate_regression_decoys": self.gate_regression_decoys,
            "r1_train": self.r1_train,
            "r1_validation": self.r1_validation,
            "r1_regression": self.r1_regression,
        }
        all_fens = [fen for values in groups.values() for fen in values]
        fullmove_numbers = [
            chess.Board(fen).fullmove_number for fen in all_fens
        ]
        r0_groups = {
            "r0_train": self.r0_train,
            "r0_validation": self.r0_validation,
            "r0_regression": self.r0_regression,
        }
        r0_strata = {
            "r0_train": self.r0_train_strata,
            "r0_validation": self.r0_validation_strata,
            "r0_regression": self.r0_regression_strata,
        }
        r0_orbits = [
            _r1_orbit_key(fen)
            for values in r0_groups.values()
            for fen in values
        ]
        r1_groups = {
            "r1_train": self.r1_train,
            "r1_validation": self.r1_validation,
            "r1_regression": self.r1_regression,
        }
        r1_strata = {
            "r1_train": self.r1_train_strata,
            "r1_validation": self.r1_validation_strata,
            "r1_regression": self.r1_regression_strata,
        }
        r1_orbits = [
            _r1_orbit_key(fen)
            for values in r1_groups.values()
            for fen in values
        ]
        retired_orbits = {
            _r1_orbit_key(fen) for fen in R1_RETIRED_DEVELOPMENT_FENS
        }
        return {
            "groups": {
                name: {"count": len(values), "sha256": _hash_json(values)}
                for name, values in groups.items()
            },
            "all_fens_disjoint": len(all_fens) == len(set(all_fens)),
            "combined_sha256": _hash_json(groups),
            "fen_fullmove_namespace": {
                "minimum": min(fullmove_numbers, default=None),
                "maximum": max(fullmove_numbers, default=None),
                "unique_count": len(set(fullmove_numbers)),
            },
            "final_test_created_or_touched": False,
            "solution_predicates_used_for": "curriculum scheduling only",
            "r0_excluded_development": {
                "count": len(self.r0_excluded_fens),
                "sha256": _hash_json(self.r0_excluded_fens),
            },
            "r0_pool_mode": self.r0_pool_mode,
            "r0_symmetry_orbits_disjoint": len(r0_orbits) == len(set(r0_orbits)),
            "r0_strata": {
                name: _stratum_manifest(r0_groups[name], labels)
                for name, labels in r0_strata.items()
            },
            "r1_pool_mode": self.r1_pool_mode,
            "r1_symmetry_orbits_disjoint": len(r1_orbits) == len(set(r1_orbits)),
            "r1_retired_development_orbit_overlap_count": sum(
                orbit in retired_orbits for orbit in r1_orbits
            ),
            "r1_strata": {
                name: _stratum_manifest(r1_groups[name], labels)
                for name, labels in r1_strata.items()
            },
        }


@dataclass(frozen=True)
class _R0ReplayExperience:
    """One outcome-grounded response remembered by the mature R0 graph.

    The move is the graph's own frozen response, not a trainer label. Replay
    still live-confirms the ReCoN branch and re-executes the move in the world.
    """

    fen: str
    move_uci: str
    triplet_id: str
    observed_terminal: str | None


def run_native_intrinsic_curriculum(
    *,
    config: NativeIntrinsicCurriculumConfig | None = None,
    r0_child_authority_factory: Callable[
        [
            NativeReConKRKGraph,
            IntrinsicCreditEngine,
            "_Pools",
            NativeIntrinsicCurriculumConfig,
        ],
        tuple[Any, Mapping[str, Any]],
    ]
    | None = None,
) -> NativeIntrinsicCurriculumResult:
    cfg = config or NativeIntrinsicCurriculumConfig()
    if (
        cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
        and cfg.r1_mechanistic_factorial
    ):
        raise ValueError(
            "v2_prospective requires the fixed full/no-bootstrap design; "
            "V2-specific mechanistic factorial arms are not defined"
        )
    run_started = perf_counter()
    pools = _build_pools(cfg)
    graph = NativeReConKRKGraph(config=_graph_config(cfg))
    ecology_uuid = hashlib.sha256(
        f"native-intrinsic-empty-graph:{cfg.seed}".encode("utf-8")
    ).hexdigest()[:24]
    graph.graph.nodes[ROOT_ID].meta["ecology_uuid"] = ecology_uuid
    credit = IntrinsicCreditEngine(_credit_config(cfg))
    credit.register(R0_COMPETENCE_ID, mature=False, hierarchy_depth=0)

    initial_graph_audit = graph.learned_state_audit()
    empty_learned_state = (
        initial_graph_audit["triplet_count"] == 0
        and initial_graph_audit["trainable_edge_count"] == 0
        and initial_graph_audit["nonzero_local_weight_node_count"] == 0
        and initial_graph_audit["m3_update_count"] == 0
    )
    if not empty_learned_state:
        raise RuntimeError("native intrinsic curriculum did not start empty")

    r0_training = _train_r0(
        graph,
        credit,
        pools.r0_train,
        pools.r0_validation,
        pools.r0_regression,
        config=cfg,
    )
    r0_validation = _evaluate_r0(graph, pools.r0_validation, max_samples=cfg.max_samples)
    r0_regression = _evaluate_r0(graph, pools.r0_regression, max_samples=cfg.max_samples)
    r0_pass = (
        r0_validation["accuracy"] >= cfg.r0_mastery_threshold
        and r0_regression["accuracy"] >= cfg.r0_mastery_threshold
        and r0_validation["illegal_move_count"] == 0
        and r0_regression["illegal_move_count"] == 0
    )

    r0_gate: OutcomeCalibratedPrototypeGate | None = None
    r0_gate_selection: dict[str, Any] | None = None
    r0_consolidation: dict[str, Any] = {
        "skipped": True,
        "reason": "r0_mastery_gate_failed",
    }
    if r0_pass:
        r0_gate, r0_gate_selection = _fit_r0_gate(
            graph,
            train_positive=pools.r0_train,
            train_negative=pools.gate_train_decoys,
            validation_positive=pools.r0_validation,
            validation_negative=pools.gate_validation_decoys,
            regression_positive=pools.r0_regression,
            regression_negative=pools.gate_regression_decoys,
        )
        enabled = r0_validation["accuracy"]
        disabled = _evaluate_r0(
            graph,
            pools.r0_validation,
            masked_triplets=set(graph.triplet_ids),
            max_samples=0,
        )["accuracy"]
        credit.set_mature(R0_COMPETENCE_ID)
        intervention = credit.record_paired_intervention(
            R0_COMPETENCE_ID,
            enabled_return=enabled,
            disabled_return=disabled,
        )
        deltas = credit.consolidate((R0_COMPETENCE_ID,))
        maturation = graph.mature_existing_graph()
        r0_consolidation = {
            "skipped": False,
            "paired_intervention": asdict(intervention),
            "value_consolidation_deltas": deltas,
            "competence": credit.snapshot()["states"][R0_COMPETENCE_ID],
            "gate": r0_gate.to_dict(),
            "gate_selection": r0_gate_selection,
            "graph_maturation": maturation,
        }

    clone_parity = _clone_parity(graph, pools.r0_regression)
    r0_replay_memory, r0_replay_memory_audit = _build_r0_replay_memory(
        graph,
        pools.r0_train,
    )
    r0_child_triplet_ids = frozenset(graph.triplet_ids)
    r0_parameter_freeze: dict[str, Any] = {
        "skipped": True,
        "reason": "disabled_or_r1_not_eligible",
    }
    if cfg.run_r1 and r0_pass and cfg.freeze_r0_parameters_for_r1:
        r0_parameter_freeze = graph.freeze_existing_parameters(
            reason="R0_joint_mastery_consolidation",
        )
    r0_child_authority: Any | None = None
    r0_child_authority_audit: dict[str, Any] = {
        "enabled": False,
        "reason": "availability_mode_is_not_v2_prospective",
    }
    if (
        cfg.run_r1
        and r0_pass
        and cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
    ):
        if r0_child_authority_factory is None:
            raise ValueError(
                "v2_prospective availability requires an explicit R0 child "
                "authority factory"
            )
        before_factory = hashlib.sha256(
            pickle.dumps((graph, credit), protocol=5)
        ).hexdigest()
        authority, authority_audit = r0_child_authority_factory(
            graph, credit, pools, cfg
        )
        after_factory = hashlib.sha256(
            pickle.dumps((graph, credit), protocol=5)
        ).hexdigest()
        if before_factory != after_factory:
            raise RuntimeError("R0 child authority construction mutated the curriculum")
        if not callable(getattr(authority, "open_virtual", None)):
            raise TypeError("R0 child authority lacks open_virtual")
        if not callable(getattr(authority, "continuation_digest", None)):
            raise TypeError("R0 child authority lacks continuation_digest")
        r0_child_authority = authority
        r0_child_authority_audit = {
            "enabled": True,
            "continuation_digest": authority.continuation_digest(),
            **dict(authority_audit),
        }
    progress: dict[str, Any] = {
        "schema_version": "krk_native_intrinsic_r0_r1_progress.v0",
        "ecology_uuid": ecology_uuid,
        "r0": {
            "pass": r0_pass,
            "validation_accuracy": r0_validation["accuracy"],
            "regression_accuracy": r0_regression["accuracy"],
            "stopped_epoch": r0_training["stopped_epoch"],
            "availability_mode": cfg.r0_availability_mode,
        },
        "completed_r1_arms": {},
    }
    _write_json(cfg.progress_path, progress)
    arms: dict[str, Any] = {}
    selected_graph = graph
    selected_credit = credit
    availability_ready = bool(
        (
            cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
            and r0_child_authority is not None
        )
        or (
            r0_gate is not None
            and (
                r0_gate.mature
                or cfg.r0_availability_mode == "virtual_frame_verified"
            )
        )
    )
    if cfg.run_r1 and r0_pass and availability_ready:
        r0_graph = copy.deepcopy(graph)
        r0_credit = copy.deepcopy(credit)
        if cfg.r1_mechanistic_factorial:
            arm_specs = _mechanistic_r1_arms(cfg)
            primary_arm_name = "exact_verify_learned_value"
        else:
            legacy_names = ["full_intrinsic", "no_bootstrap"]
            if cfg.run_redundant_child_ablation:
                legacy_names.append("child_ablation")
            arm_specs = tuple(_legacy_r1_arm(name, cfg) for name in legacy_names)
            primary_arm_name = "full_intrinsic"
        for arm_spec in arm_specs:
            arm_name = arm_spec.name
            if cfg.r1_mechanistic_factorial or arm_name == primary_arm_name:
                arm_epoch_budget = cfg.r1_epochs
            else:
                arm_epoch_budget = int(
                    arms[primary_arm_name]["training"]["stopped_epoch"]
                )
            arm_graph = copy.deepcopy(r0_graph)
            arm_credit = copy.deepcopy(r0_credit)
            arms[arm_name] = _run_r1_arm(
                arm_name,
                arm_graph,
                arm_credit,
                r0_gate,
                pools,
                r0_replay_memory=r0_replay_memory,
                r0_child_triplet_ids=r0_child_triplet_ids,
                max_epochs=arm_epoch_budget,
                config=cfg,
                arm_spec=arm_spec,
                r0_child_authority=r0_child_authority,
                run_started=run_started,
            )
            if arm_name == primary_arm_name:
                selected_graph = arm_graph
                selected_credit = arm_credit
            progress["completed_r1_arms"][arm_name] = _arm_progress_summary(
                arms[arm_name]
            )
            progress.pop("active_r1_arm", None)
            _write_json(cfg.progress_path, progress)

        full_rate = arms[primary_arm_name]["regression"]["conversion_rate"]
        no_bootstrap_rate = arms["no_bootstrap"]["regression"]["conversion_rate"]
        full_pass = (
            arms[primary_arm_name]["validation"]["conversion_rate"]
            >= cfg.r1_mastery_threshold
            and full_rate >= cfg.r1_mastery_threshold
            and arms[primary_arm_name]["r0_retention"]["accuracy"]
            >= cfg.r0_mastery_threshold
        )
        if full_pass:
            selected_credit.set_mature(R1_COMPETENCE_ID)
            intervention = selected_credit.record_paired_intervention(
                R1_COMPETENCE_ID,
                enabled_return=full_rate,
                disabled_return=no_bootstrap_rate,
            )
            graph_maturation = selected_graph.mature_existing_graph()
            parameter_freeze = selected_graph.freeze_existing_parameters(
                reason="R1_joint_mastery_consolidation",
            )
            arms[primary_arm_name]["consolidation"] = {
                "paired_intervention": asdict(intervention),
                "value_consolidation_deltas": selected_credit.consolidate(
                    (R1_COMPETENCE_ID,)
                ),
                "graph_maturation": graph_maturation,
                "parameter_freeze": parameter_freeze,
            }

    r1_executed = bool(arms)
    primary_arm_name = (
        "exact_verify_learned_value"
        if cfg.r1_mechanistic_factorial
        else "full_intrinsic"
    )
    r1_pass = bool(
        r1_executed
        and arms[primary_arm_name]["validation"]["conversion_rate"]
        >= cfg.r1_mastery_threshold
        and arms[primary_arm_name]["regression"]["conversion_rate"]
        >= cfg.r1_mastery_threshold
        and arms[primary_arm_name]["r0_retention"]["accuracy"]
        >= cfg.r0_mastery_threshold
    )
    development_directional_effect = bool(
        r1_executed
        and arms[primary_arm_name]["validation"]["conversion_rate"]
        > arms["no_bootstrap"]["validation"]["conversion_rate"]
        and arms[primary_arm_name]["regression"]["conversion_rate"]
        > arms["no_bootstrap"]["regression"]["conversion_rate"]
    )
    # A single development seed cannot establish a causal positive result.
    # Preserve the old field for consumers, but require a future preregistered
    # replicated analysis to set it true.
    causal_positive = False

    payload = {
        "scientific_contract": {
            "empty_means_empty_learned_state_not_absent_embodiment": True,
            "one_persistent_graph_across_rungs": True,
            "ecology_uuid": ecology_uuid,
            "native_formal_confirmation_used": True,
            "python_weighted_arbitration_used": True,
            "pure_in_graph_arbitration_claimed": False,
            "training_exploration": (
                "content_blind_round_robin_over_formally_confirmed_legal_action_branches"
            ),
            "learner_visible_stage_labels": False,
            "correct_move_labels_used_for_training_credit": False,
            "forced_move_labels_used_for_training_credit": False,
            "geometry_reward_used": False,
            "validator_verdict_used_for_reward": False,
            "runtime_tablebase_or_dtm_move_source": False,
            "reward_channels": [
                "observed_world_terminal",
                "real_move_metabolic_cost",
                "mature_outcome_grounded_child_value",
            ],
            "curriculum_solution_predicates_trainer_side_only": True,
            "r0_availability_mode": cfg.r0_availability_mode,
            "mechanistic_factorial_enabled": cfg.r1_mechanistic_factorial,
            "exact_virtual_verification_is_oracle_control_not_autonomy_evidence": True,
            "prototype_gate_is_learned_but_host_side": True,
            "composition_disabled_in_mechanistic_factorial": (
                cfg.r1_mechanistic_factorial
            ),
            "td_prediction_source": "exact_unrounded_confirmed_graph_action_score",
            "policy_score_and_td_prediction_identical": True,
            "virtual_frames_create_grounding": False,
            "r0_replay_cache_used_as_provider": False,
            "r0_parameters_frozen_for_r1": cfg.freeze_r0_parameters_for_r1,
            "r0_child_queries_scoped_to_frozen_snapshot": True,
            "r0_child_dispatch_cache_used_as_external_provider": False,
            "r0_child_dispatch_cache_is_memoized_graph_response": True,
            "r0_child_dispatch_hits_live_formally_confirmed": (
                cfg.r0_child_cache_validation_mode == "live_formal"
            ),
            "r0_child_dispatch_hits_frozen_policy_certified": (
                cfg.r0_child_cache_validation_mode == "frozen_policy_token"
            ),
            "runtime_child_priority_uses_stage_labels": False,
            "runtime_mature_child_priority_is_arm_specific": True,
            "runtime_child_priority_source": "explicit_mechanistic_arm",
            "v2_child_authority_derived_from_same_run_r0": bool(
                r0_child_authority is not None
            ),
            "v2_virtual_child_queries_are_read_only": bool(
                r0_child_authority is not None
            ),
            "v2_real_training_evidence_is_append_only": bool(
                r0_child_authority is not None
            ),
            "v2_same_event_outcome_cannot_bootstrap_itself": bool(
                r0_child_authority is not None
            ),
            "r1_reply_schedule": "per_position_action_content_blind_round_robin",
            "serialized_interval_snapshot_resume_implemented": True,
            "snapshot_resume_requires_exact_fingerprint": True,
            "immutable_checkpoint_history_enabled": cfg.r1_keep_checkpoint_history,
            "source_and_dependency_identity_fingerprinted": True,
            "r0_replay_cache_semantics": (
                "memoized_mature_graph_response_live_formal_reconfirmation_"
                "and_world_reexecution"
            ),
        },
        "source_identity": _source_identity(),
        "pool_manifest": pools.manifest(),
        "progress_path": cfg.progress_path,
        "initial_graph_audit": initial_graph_audit,
        "initial_graph_sha256": _hash_json(initial_graph_audit),
        "r0": {
            "training": r0_training,
            "validation": r0_validation,
            "regression": r0_regression,
            "consolidation": r0_consolidation,
            "pass": r0_pass,
        },
        "clone_resume_probe": clone_parity,
        "r0_replay_memory": r0_replay_memory_audit,
        "r0_parameter_freeze": r0_parameter_freeze,
        "r0_child_authority": r0_child_authority_audit,
        "r1_arms": arms,
        "final_graph": selected_graph.to_dict(),
        "final_credit": selected_credit.snapshot(),
        "decision": {
            "r0_pass": r0_pass,
            "r1_executed": r1_executed,
            "r1_pass": r1_pass,
            "primary_upper_bound_arm": primary_arm_name,
            "development_directional_effect_vs_no_bootstrap": development_directional_effect,
            "r1_causal_positive_vs_no_bootstrap": causal_positive,
            "causal_claim_locked_pending_preregistered_seed_replication": True,
            "advance_to_r2": False,
            "interpretation": (
                "development_factorial_complete_no_r2_without_replication"
                if r1_executed
                else "r0_failed_or_gate_unavailable_do_not_advance"
            ),
        },
    }
    return NativeIntrinsicCurriculumResult(config=cfg, payload=payload)


def _graph_config(cfg: NativeIntrinsicCurriculumConfig) -> NativeSingleGraphConfig:
    return NativeSingleGraphConfig(
        include_symmetries=False,
        train_repetitions=1,
        continuation_repetitions=1,
        eta_m3=cfg.eta_m3,
        max_ticks=cfg.max_ticks,
        indexed_scheduler=True,
        tick_feature_terminals=False,
        key_mode="canonical",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        shared_atom_min_overlap=2,
        max_shared_atom_candidates_per_choice=64,
        max_prototype_candidates_per_move=16,
        max_prototype_scan_triplets=512,
        score_action_pattern_atoms=True,
        score_hierarchy_edge_weights=False,
        terminal_score_normalization="sqrt",
    )


def _credit_config(cfg: NativeIntrinsicCurriculumConfig) -> IntrinsicCreditConfig:
    return IntrinsicCreditConfig(
        eta_fast=cfg.eta_fast,
        eta_slow=cfg.eta_slow,
        real_move_cost=cfg.real_move_cost,
        min_grounding_evidence=cfg.min_grounding_evidence,
        min_causal_confirmations=1,
    )


def _build_pools(cfg: NativeIntrinsicCurriculumConfig) -> _Pools:
    used: set[str] = set(cfg.r0_excluded_fens)

    def m1(count: int, offset: int) -> tuple[str, ...]:
        values = tuple(
            _generate_mate_in_one_positions(
                count=count,
                seed=cfg.seed + offset,
                excluded=used,
                max_attempts=cfg.max_generation_attempts,
            )
        )
        used.update(values)
        return values

    def m2(count: int, offset: int) -> tuple[str, ...]:
        values = tuple(
            _generate_forced_mate_in_two_positions(
                count=count,
                seed=cfg.seed + offset,
                excluded=used,
                max_attempts=cfg.max_generation_attempts,
            )
        )
        used.update(values)
        return values

    if cfg.r0_pool_mode == "random":
        r0_train = m1(cfg.r0_train_count, 0)
        r0_validation = m1(cfg.r0_validation_count, 1)
        r0_regression = m1(cfg.r0_regression_count, 2)
        r0_train_strata = tuple("random" for _ in r0_train)
        r0_validation_strata = tuple("random" for _ in r0_validation)
        r0_regression_strata = tuple("random" for _ in r0_regression)
    elif cfg.r0_pool_mode == "balanced_location":
        used_orbits = {_r1_orbit_key(fen) for fen in cfg.r0_excluded_fens}
        r0_train, r0_train_strata = _generate_balanced_r0_split(
            count=cfg.r0_train_count,
            seed=cfg.seed,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
        r0_validation, r0_validation_strata = _generate_balanced_r0_split(
            count=cfg.r0_validation_count,
            seed=cfg.seed + 1,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
        r0_regression, r0_regression_strata = _generate_balanced_r0_split(
            count=cfg.r0_regression_count,
            seed=cfg.seed + 2,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
    else:
        raise ValueError("r0_pool_mode must be random or balanced_location")
    gate_train_decoys = _generate_non_m1_positions(
        count=cfg.r0_gate_train_decoy_count,
        seed=cfg.seed + 3,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    )
    used.update(gate_train_decoys)
    gate_validation_decoys = _generate_non_m1_positions(
        count=cfg.r0_gate_validation_decoy_count,
        seed=cfg.seed + 4,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    )
    used.update(gate_validation_decoys)
    gate_regression_decoys = _generate_non_m1_positions(
        count=cfg.r0_gate_regression_decoy_count,
        seed=cfg.seed + 5,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    )
    used.update(gate_regression_decoys)
    if not cfg.run_r1:
        r1_train = r1_validation = r1_regression = ()
        r1_train_strata = r1_validation_strata = r1_regression_strata = ()
    elif cfg.r1_pool_mode == "random":
        r1_train = m2(cfg.r1_train_count, 6)
        r1_validation = m2(cfg.r1_validation_count, 7)
        r1_regression = m2(cfg.r1_regression_count, 8)
        r1_train_strata = tuple("random" for _ in r1_train)
        r1_validation_strata = tuple("random" for _ in r1_validation)
        r1_regression_strata = tuple("random" for _ in r1_regression)
    elif cfg.r1_pool_mode == "balanced_setup":
        used_orbits = {
            _r1_orbit_key(fen) for fen in R1_RETIRED_DEVELOPMENT_FENS
        }
        r1_train, r1_train_strata = _generate_balanced_r1_split(
            count=cfg.r1_train_count,
            seed=cfg.seed + 6,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
        r1_validation, r1_validation_strata = _generate_balanced_r1_split(
            count=cfg.r1_validation_count,
            seed=cfg.seed + 7,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
        r1_regression, r1_regression_strata = _generate_balanced_r1_split(
            count=cfg.r1_regression_count,
            seed=cfg.seed + 8,
            used_fens=used,
            used_orbits=used_orbits,
            max_attempts=cfg.max_generation_attempts,
        )
    else:
        raise ValueError("r1_pool_mode must be random or balanced_setup")
    if cfg.development_fen_fullmove_base is not None:
        (
            r0_train,
            r0_validation,
            r0_regression,
            gate_train_decoys,
            gate_validation_decoys,
            gate_regression_decoys,
            r1_train,
            r1_validation,
            r1_regression,
        ) = _namespace_development_fullmoves(
            (
                r0_train,
                r0_validation,
                r0_regression,
                gate_train_decoys,
                gate_validation_decoys,
                gate_regression_decoys,
                r1_train,
                r1_validation,
                r1_regression,
            ),
            base=int(cfg.development_fen_fullmove_base),
        )
    return _Pools(
        r0_train=r0_train,
        r0_validation=r0_validation,
        r0_regression=r0_regression,
        gate_train_decoys=tuple(gate_train_decoys),
        gate_validation_decoys=tuple(gate_validation_decoys),
        gate_regression_decoys=tuple(gate_regression_decoys),
        r1_train=r1_train,
        r1_validation=r1_validation,
        r1_regression=r1_regression,
        r0_train_strata=r0_train_strata,
        r0_validation_strata=r0_validation_strata,
        r0_regression_strata=r0_regression_strata,
        r0_excluded_fens=tuple(cfg.r0_excluded_fens),
        r0_pool_mode=cfg.r0_pool_mode,
        r1_train_strata=r1_train_strata,
        r1_validation_strata=r1_validation_strata,
        r1_regression_strata=r1_regression_strata,
        r1_pool_mode=cfg.r1_pool_mode,
    )


def _namespace_development_fullmoves(
    groups: Sequence[Sequence[str]],
    *,
    base: int,
) -> tuple[tuple[str, ...], ...]:
    """Give viewed development inputs an exact physical-identity namespace."""

    if base < 10_000:
        raise ValueError("development FEN fullmove base must be at least 10,000")
    ordinal = 0
    result: list[tuple[str, ...]] = []
    for group in groups:
        namespaced: list[str] = []
        for fen in group:
            board = chess.Board(fen)
            if board.fullmove_number != 1:
                raise ValueError(
                    "development FEN namespace expects generated fullmove number 1"
                )
            board.fullmove_number = base + ordinal
            namespaced.append(board.fen())
            ordinal += 1
        result.append(tuple(namespaced))
    return tuple(result)


def _balanced_r0_quotas(count: int) -> dict[str, int]:
    if count <= 0 or count % 8 != 0:
        raise ValueError(
            "balanced_location R0 split counts must be positive multiples of 8"
        )
    return {label: count // 8 for label in R0_BALANCED_STRATA}


def _generate_balanced_r0_split(
    *,
    count: int,
    seed: int,
    used_fens: set[str],
    used_orbits: set[str],
    max_attempts: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    quotas = _balanced_r0_quotas(count)
    accepted = {label: 0 for label in quotas}
    positions: list[str] = []
    labels: list[str] = []
    rng = random.Random(seed)
    for _attempt in range(max_attempts):
        if len(positions) >= count:
            break
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        mates = _mate_moves(board)
        if not 1 <= len(mates) <= 3:
            continue
        label = _classify_r0_stratum(board)
        if label is None or accepted[label] >= quotas[label]:
            continue
        fen = board.fen()
        orbit = _r1_orbit_key(fen)
        if fen in used_fens or orbit in used_orbits:
            continue
        used_fens.add(fen)
        used_orbits.add(orbit)
        positions.append(fen)
        labels.append(label)
        accepted[label] += 1
    unmet = {
        label: quotas[label] - accepted[label]
        for label in quotas
        if accepted[label] < quotas[label]
    }
    if unmet:
        raise RuntimeError(
            f"balanced R0 generation produced {len(positions)}/{count}; unmet={unmet}"
        )
    return tuple(positions), tuple(labels)


def _classify_r0_stratum(board: chess.Board) -> str | None:
    location_kind, location = _black_king_location(board)
    if location_kind not in {"edge", "corner"}:
        return None
    return f"black_king_{location_kind}:{location}"


def _balanced_r1_quotas(count: int) -> dict[str, int]:
    if count <= 0 or count % 16 != 0:
        raise ValueError("balanced_setup R1 split counts must be positive multiples of 16")
    return {
        **{f"rook_barrier:{side}": count // 8 for side in ("left", "right", "bottom", "top")},
        **{f"king_edge:{side}": count // 16 for side in ("left", "right", "bottom", "top")},
        **{f"king_corner:{corner}": count // 16 for corner in ("a1", "a8", "h1", "h8")},
    }


def _generate_balanced_r1_split(
    *,
    count: int,
    seed: int,
    used_fens: set[str],
    used_orbits: set[str],
    max_attempts: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    quotas = _balanced_r1_quotas(count)
    accepted = {label: 0 for label in quotas}
    positions: list[str] = []
    labels: list[str] = []
    rng = random.Random(seed)
    for _attempt in range(max_attempts):
        if len(positions) >= count:
            break
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        forced = tuple(_forced_mate_in_two_first_moves(board))
        if not forced:
            continue
        label = _classify_r1_stratum(board, forced)
        if label is None or accepted.get(label, 0) >= quotas.get(label, 0):
            continue
        fen = board.fen()
        orbit = _r1_orbit_key(fen)
        if fen in used_fens or orbit in used_orbits:
            continue
        used_fens.add(fen)
        used_orbits.add(orbit)
        positions.append(fen)
        labels.append(label)
        accepted[label] += 1
    unmet = {
        label: quotas[label] - accepted[label]
        for label in quotas
        if accepted[label] < quotas[label]
    }
    if unmet:
        raise RuntimeError(
            f"balanced R1 generation produced {len(positions)}/{count}; unmet={unmet}"
        )
    return tuple(positions), tuple(labels)


def _classify_r1_stratum(
    board: chess.Board,
    forced_moves: Sequence[chess.Move],
) -> str | None:
    location_kind, location = _black_king_location(board)
    king_moves = [
        move
        for move in forced_moves
        if board.piece_at(move.from_square).piece_type == chess.KING
    ]
    if location_kind == "corner":
        return f"king_corner:{location}" if king_moves else None
    if location_kind != "edge":
        return None
    expected_rook_axis = "file" if location in {"left", "right"} else "rank"
    for move in forced_moves:
        piece = board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.ROOK:
            continue
        axis = (
            "file"
            if chess.square_file(move.from_square) == chess.square_file(move.to_square)
            else "rank"
        )
        if axis == expected_rook_axis:
            return f"rook_barrier:{location}"
    return f"king_edge:{location}" if king_moves else None


def _black_king_location(board: chess.Board) -> tuple[str, str]:
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return "missing", "missing"
    file_idx = chess.square_file(black_king)
    rank_idx = chess.square_rank(black_king)
    if file_idx in (0, 7) and rank_idx in (0, 7):
        return "corner", chess.square_name(black_king)
    if file_idx == 0:
        return "edge", "left"
    if file_idx == 7:
        return "edge", "right"
    if rank_idx == 0:
        return "edge", "bottom"
    if rank_idx == 7:
        return "edge", "top"
    return "interior", "interior"


def _r1_orbit_key(fen: str) -> str:
    board = chess.Board(fen)
    squares = (
        board.king(chess.WHITE),
        next(iter(board.pieces(chess.ROOK, chess.WHITE)), None),
        board.king(chess.BLACK),
    )
    if any(square is None for square in squares):
        raise ValueError("R1 orbit key requires white king, white rook, and black king")
    variants: list[tuple[int, int, int]] = []
    for transform_index in range(8):
        transformed: list[int] = []
        for square in squares:
            file_idx = chess.square_file(square)
            rank_idx = chess.square_rank(square)
            coordinates = (
                (file_idx, rank_idx),
                (7 - file_idx, rank_idx),
                (file_idx, 7 - rank_idx),
                (7 - file_idx, 7 - rank_idx),
                (rank_idx, file_idx),
                (7 - rank_idx, file_idx),
                (rank_idx, 7 - file_idx),
                (7 - rank_idx, 7 - file_idx),
            )
            transformed.append(chess.square(*coordinates[transform_index]))
        variants.append(tuple(transformed))
    return ":".join(str(square) for square in min(variants))


def _stratum_manifest(
    fens: Sequence[str],
    labels: Sequence[str],
) -> dict[str, Any]:
    if len(fens) != len(labels):
        raise ValueError("R1 FEN and stratum sequences must align")
    grouped: dict[str, list[str]] = {}
    for fen, label in zip(fens, labels, strict=True):
        grouped.setdefault(label, []).append(fen)
    return {
        "labels_sha256": _hash_json(labels),
        "groups": {
            label: {
                "count": len(values),
                "sha256": _hash_json(tuple(values)),
            }
            for label, values in sorted(grouped.items())
        },
    }

def _train_r0(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    train_fens: Sequence[str],
    validation_fens: Sequence[str],
    regression_fens: Sequence[str],
    *,
    config: NativeIntrinsicCurriculumConfig,
) -> dict[str, Any]:
    episodes = mates = nonterminal = failures = 0
    started = perf_counter()
    formal_confirmation_failures = 0
    checkpoints: list[dict[str, Any]] = []
    stopped_epoch = config.r0_epochs
    for epoch in range(config.r0_epochs):
        for position_index, fen in enumerate(train_fens):
            board = chess.Board(fen)
            move, triplet_id, confirmed, graph_prediction = _scheduled_confirmed_action(
                graph,
                board,
                schedule_index=epoch + position_index,
                stage_diagnostic="R0_mate_in_1",
            )
            formal_confirmation_failures += int(not confirmed)
            terminal_kind = _execute_white_and_observe(board, move)
            credit.register(triplet_id, hierarchy_depth=1)
            credit.begin_episode()
            event = credit.transition(
                triplet_id,
                responsibilities=(
                    Responsibility(triplet_id, parent_distance=0),
                    Responsibility(R0_COMPETENCE_ID, parent_distance=1),
                ),
                terminal_kind=terminal_kind,
                prediction_override=graph_prediction,
            )
            graph.apply_intrinsic_td(
                board,
                move,
                td_error=event.td_error,
                stage_diagnostic="R0_mate_in_1",
            )
            episodes += 1
            mates += int(terminal_kind == "mate")
            failures += int(terminal_kind in {"stalemate", "rook_loss", "illegal"})
            nonterminal += int(terminal_kind is None)
        should_validate = (
            epoch == 0
            or epoch == config.r0_epochs - 1
            or (epoch + 1) % max(1, config.r0_validation_interval) == 0
        )
        if not should_validate:
            continue
        metrics = _evaluate_r0(graph, validation_fens, max_samples=0)
        checkpoint = {
            "epoch": epoch + 1,
            "validation_accuracy": metrics["accuracy"],
            "triplet_count": len(graph.triplet_ids),
            "m3_update_count": graph.m3_update_count,
        }
        if metrics["accuracy"] >= config.r0_mastery_threshold:
            confirmation = _evaluate_r0(graph, regression_fens, max_samples=0)
            checkpoint["regression_accuracy_at_mastery_probe"] = confirmation["accuracy"]
            checkpoint["joint_mastery"] = (
                confirmation["accuracy"] >= config.r0_mastery_threshold
            )
            if checkpoint["joint_mastery"]:
                stopped_epoch = epoch + 1
                checkpoints.append(checkpoint)
                break
        checkpoints.append(checkpoint)
    return {
        "episodes": episodes,
        "observed_mate_count": mates,
        "observed_nonterminal_count": nonterminal,
        "observed_failure_count": failures,
        "formal_confirmation_failure_count": formal_confirmation_failures,
        "stopped_epoch": stopped_epoch,
        "validation_checkpoints": checkpoints,
        "teacher_positive_move_sets_consumed": 0,
        "forced_first_move_labels_consumed": 0,
        "graph_after_training": graph.learned_state_audit(),
        "duration_seconds": round(perf_counter() - started, 6),
    }


class R1CheckpointInterrupt(RuntimeError):
    """Test/diagnostic interruption raised only after an atomic R1 snapshot."""

    def __init__(self, *, epoch: int, snapshot_path: Path) -> None:
        super().__init__(f"R1 interrupted after epoch {epoch}; snapshot={snapshot_path}")
        self.epoch = int(epoch)
        self.snapshot_path = snapshot_path


class R1DevelopmentCeilingReached(RuntimeError):
    """Raised at an epoch boundary after persisting an exact R1 snapshot."""

    def __init__(
        self, *, epoch: int, snapshot_path: Path, reason: str
    ) -> None:
        super().__init__(
            f"R1 development ceiling reached after epoch {epoch}; "
            f"reason={reason}; snapshot={snapshot_path}"
        )
        self.epoch = int(epoch)
        self.snapshot_path = snapshot_path
        self.reason = str(reason)


def _peak_rss_mib() -> float:
    raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return raw / (1024.0 * 1024.0) if platform.system() == "Darwin" else raw / 1024.0


def _development_ceiling_reason(
    config: NativeIntrinsicCurriculumConfig,
    *,
    run_started: float,
) -> str | None:
    elapsed = perf_counter() - run_started
    if (
        config.development_wall_ceiling_seconds is not None
        and elapsed >= float(config.development_wall_ceiling_seconds)
    ):
        return (
            f"wall_seconds={elapsed:.3f}>="
            f"{float(config.development_wall_ceiling_seconds):.3f}"
        )
    peak = _peak_rss_mib()
    if (
        config.development_peak_rss_ceiling_mib is not None
        and peak >= float(config.development_peak_rss_ceiling_mib)
    ):
        return (
            f"peak_rss_mib={peak:.3f}>="
            f"{float(config.development_peak_rss_ceiling_mib):.3f}"
        )
    return None


def _package_version(*names: str) -> str:
    for name in names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "not-installed-as-distribution"


@lru_cache(maxsize=1)
def _source_identity() -> dict[str, Any]:
    """Behavior identity used by artifacts and resume fingerprints."""

    repo_root = Path(__file__).resolve().parents[3]

    def git(*args: str) -> str:
        result = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unavailable"

    behavior_files = (
        Path(__file__).resolve(),
        Path(__file__).with_name("native_single_graph_curriculum.py").resolve(),
        Path(__file__).with_name("native_authority_handover.py").resolve(),
        Path(__file__).with_name("native_competence_envelope.py").resolve(),
        Path(__file__).with_name("native_trace_competence_authority.py").resolve(),
        Path(__file__).with_name(
            "native_prospective_evidence_authority_v2.py"
        ).resolve(),
        (repo_root / "src/recon_lite_hector/learning/intrinsic_credit.py").resolve(),
    )
    return {
        "git_commit": git("rev-parse", "HEAD"),
        "tracked_worktree_status_sha256": hashlib.sha256(
            git("status", "--short", "--untracked-files=no").encode("utf-8")
        ).hexdigest(),
        "behavior_file_sha256": {
            str(path.relative_to(repo_root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in behavior_files
        },
        "python": platform.python_version(),
        "python_chess": _package_version("python-chess", "chess"),
    }


def _r1_snapshot_path(
    config: NativeIntrinsicCurriculumConfig,
    pools: _Pools,
    arm_name: str,
) -> Path:
    pool_hash = str(pools.manifest()["combined_sha256"])[:16]
    return Path(config.r1_snapshot_dir) / f"seed_{config.seed}_{pool_hash}_{arm_name}.pkl"


def _r1_history_snapshot_path(
    config: NativeIntrinsicCurriculumConfig,
    pools: _Pools,
    arm_name: str,
    epoch: int,
) -> Path:
    pool_hash = str(pools.manifest()["combined_sha256"])[:16]
    return (
        Path(config.r1_snapshot_dir)
        / "history"
        / f"seed_{config.seed}_{pool_hash}_{arm_name}_epoch_{int(epoch):06d}.pkl"
    )


def _r1_base_state_identity(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    r0_child_triplet_ids: frozenset[str],
) -> dict[str, Any]:
    """Return a canonical, process-stable identity for the R1 base state.

    Raw pickle bytes are not an identity: the graph contains sets whose pickle
    order changes with ``PYTHONHASHSEED``.  The frozen policy token covers the
    executable topology and parameters, while the remaining sorted indexes and
    lifecycle fields cover graph-owned retrieval and structural state.
    """

    policy_sha256 = graph.frozen_child_policy_token(r0_child_triplet_ids)
    if policy_sha256 is None:
        policy_sha256 = graph._compute_frozen_policy_token(
            r0_child_triplet_ids
        )

    return {
        "schema": "native_intrinsic_r1_base_state.v2",
        "policy_sha256": policy_sha256,
        # The frozen token is deliberately compact.  The semantic manifest
        # additionally binds ordered graph rows and derived indexes, every
        # graph-owned retrieval/composite index, cached prototype keys, and
        # verified trainable-edge aliases.
        "graph_semantic_state_sha256": _hash_json(
            graph.canonical_semantic_manifest()
        ),
        "credit_event_index": int(credit.event_index),
        "credit": credit.snapshot(),
    }


def _r1_snapshot_fingerprint(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    r0_gate: OutcomeCalibratedPrototypeGate,
    pools: _Pools,
    *,
    arm_name: str,
    arm_spec: R1MechanisticArm,
    r0_child_triplet_ids: frozenset[str],
    r0_child_authority_digest: str | None,
    config: NativeIntrinsicCurriculumConfig,
) -> str:
    behavior_config = asdict(config)
    for key in (
        "output_path",
        "progress_path",
        "r1_snapshot_dir",
        "resume_r1_snapshots",
        "r1_keep_checkpoint_history",
        "max_samples",
        "development_wall_ceiling_seconds",
        "development_peak_rss_ceiling_mib",
    ):
        behavior_config.pop(key, None)
    payload = {
        "schema": "native_intrinsic_r1_resume.v2",
        "arm_name": arm_name,
        "arm_spec": asdict(arm_spec),
        "behavior_config": behavior_config,
        "pool_manifest": pools.manifest(),
        "r0_gate": r0_gate.to_dict(),
        "r0_child_triplet_ids": sorted(r0_child_triplet_ids),
        "r0_child_authority_digest": r0_child_authority_digest,
        "source_identity": _source_identity(),
        "base_state_sha256": _hash_json(
            _r1_base_state_identity(
                graph,
                credit,
                r0_child_triplet_ids,
            )
        ),
    }
    return _hash_json(payload)


def _atomic_pickle(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        pickle.dump(dict(payload), handle, protocol=5)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _load_r1_snapshot(path: Path, *, expected_fingerprint: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    if payload.get("schema_version") != "native_intrinsic_r1_arm_snapshot.v1":
        raise ValueError(f"unsupported R1 arm snapshot schema in {path}")
    actual = str(payload.get("fingerprint", ""))
    if actual != expected_fingerprint:
        raise ValueError(
            f"R1 snapshot fingerprint mismatch for {path}: {actual} != {expected_fingerprint}"
        )
    return payload


def _replace_object_state(target: Any, restored: Any) -> None:
    target.__dict__.clear()
    target.__dict__.update(restored.__dict__)


def _write_live_r1_progress(
    config: NativeIntrinsicCurriculumConfig,
    *,
    arm_name: str,
    epoch: int,
    checkpoint: Mapping[str, Any],
    snapshot_path: Path,
    resumed: bool,
) -> None:
    path = Path(config.progress_path)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": "krk_native_intrinsic_r0_r1_progress.v0"}
    payload["active_r1_arm"] = {
        "arm_name": arm_name,
        "epoch": int(epoch),
        "validation_conversion_rate": checkpoint.get("validation_conversion_rate"),
        "r0_retention_accuracy": checkpoint.get("r0_retention_accuracy"),
        "child_handoff_count": checkpoint.get("child_handoff_count", 0),
        "snapshot_path": str(snapshot_path),
        "resumed_from_snapshot": bool(resumed),
    }
    _write_json(path, payload)


def _shuffled_gate_schedule(
    graph: NativeReConKRKGraph,
    gate: OutcomeCalibratedPrototypeGate,
    pools: _Pools,
    *,
    r0_child_triplet_ids: frozenset[str],
    epoch_budget: int,
    seed: int,
) -> tuple[tuple[bool, ...], dict[str, Any]]:
    """Build an exactly rate-matched permutation over scheduled R1 queries."""

    started = perf_counter()
    reply_exposures: dict[tuple[str, str], int] = {}
    original: list[bool] = []
    for epoch in range(epoch_budget):
        for position_index, fen in enumerate(pools.r1_train):
            board = chess.Board(fen)
            legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
            move = legal[(epoch + position_index) % len(legal)]
            after_first = board.copy(stack=False)
            after_first.push(move)
            if _terminal_kind(after_first) is not None:
                continue
            replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
            if not replies:
                continue
            reply_key = (fen, move.uci())
            reply_index = reply_exposures.get(reply_key, 0)
            reply = replies[reply_index % len(replies)]
            reply_exposures[reply_key] = reply_index + 1
            successor = after_first.copy(stack=False)
            successor.push(reply)
            if _terminal_kind(successor) is not None:
                continue
            available, _response = _r0_available(
                graph,
                gate,
                successor,
                mode="prototype_gate",
                allowed_triplets=r0_child_triplet_ids,
            )
            original.append(bool(available))

    shuffled = list(original)
    random.Random(int(seed)).shuffle(shuffled)
    if len(shuffled) > 1 and shuffled == original and len(set(shuffled)) > 1:
        shuffled = shuffled[1:] + shuffled[:1]
    discordant = sum(left != right for left, right in zip(original, shuffled))
    return tuple(shuffled), {
        "query_count": len(original),
        "positive_count": sum(original),
        "positive_rate": 0.0 if not original else sum(original) / len(original),
        "discordant_assignment_count": discordant,
        "exact_rate_match": sum(original) == sum(shuffled),
        "seed": int(seed),
        "duration_seconds": round(perf_counter() - started, 6),
    }


def _run_r1_arm(
    arm_name: str,
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    r0_gate: OutcomeCalibratedPrototypeGate,
    pools: _Pools,
    *,
    r0_replay_memory: Sequence[_R0ReplayExperience],
    r0_child_triplet_ids: frozenset[str],
    max_epochs: int,
    config: NativeIntrinsicCurriculumConfig,
    stop_after_epoch: int | None = None,
    arm_spec: R1MechanisticArm | None = None,
    r0_child_authority: Any | None = None,
    run_started: float | None = None,
) -> dict[str, Any]:
    arm = arm_spec or _legacy_r1_arm(arm_name, config)
    if arm.name != arm_name:
        raise ValueError(f"arm name mismatch: {arm.name} != {arm_name}")
    graph.config = replace(
        graph.config,
        score_hierarchy_edge_weights=arm.hierarchy_edge_scoring,
    )
    child_value_control = _apply_child_value_control(credit, arm, config)
    if r0_child_authority is not None:
        authority_type = type(r0_child_authority)
        r0_child_authority = authority_type.loads(r0_child_authority.dumps())
        if r0_child_authority.pending_event is not None:
            raise RuntimeError("R1 child authority clone has a pending REAL event")
    epoch_budget = max(1, int(max_epochs))
    if config.r1_validation_interval <= 0 or config.r1_snapshot_interval <= 0:
        raise ValueError("R1 validation and snapshot intervals must be positive")
    snapshot_path = _r1_snapshot_path(config, pools, arm_name)
    fingerprint = _r1_snapshot_fingerprint(
        graph,
        credit,
        r0_gate,
        pools,
        arm_name=arm_name,
        arm_spec=arm,
        r0_child_triplet_ids=r0_child_triplet_ids,
        r0_child_authority_digest=(
            None
            if r0_child_authority is None
            else str(r0_child_authority.continuation_digest())
        ),
        config=config,
    )
    restored = (
        _load_r1_snapshot(snapshot_path, expected_fingerprint=fingerprint)
        if config.resume_r1_snapshots
        else None
    )
    started = perf_counter()
    resumed_from_snapshot = restored is not None
    snapshot_writes = 0
    duration_before_resume = 0.0
    if restored is None:
        credit.register(R1_COMPETENCE_ID, mature=False, hierarchy_depth=0)
        start_epoch = 0
        counters = {
            "episodes": 0,
            "child_handoffs": 0,
            "failures": 0,
            "formal_confirmation_failures": 0,
            "virtual_frame_queries": 0,
            "replay_episodes": 0,
            "replay_mates": 0,
            "replay_nonmates": 0,
            "replay_confirmation_failures": 0,
            "replay_outcome_mismatches": 0,
            "replay_seconds": 0.0,
            "child_dispatch_cache_hits": 0,
            "child_dispatch_cache_misses": 0,
            "child_dispatch_cache_mismatches": 0,
            "child_dispatch_cache_certified_hits": 0,
            "availability_queries": 0,
            "availability_positives": 0,
            "successor_value_sum": 0.0,
            "v2_real_observations": 0,
            "v2_duplicate_virtual_queries": 0,
            "v2_structural_transitions": 0,
        }
        reply_orbits: set[tuple[str, str, str]] = set()
        reply_exposure_counts: dict[tuple[str, str], int] = {}
        child_dispatch_cache: dict[str, dict[str, Any]] = {}
        checkpoints: list[dict[str, Any]] = []
        composition_events: list[dict[str, Any]] = []
        composition_consolidation_events: list[dict[str, Any]] = []
        v2_structural_events: list[dict[str, Any]] = []
        history_snapshot_paths: list[str] = []
        stopped_epoch = epoch_budget
        joint_mastery = False
    else:
        saved_budget = int(restored["epoch_budget"])
        if saved_budget != epoch_budget:
            raise ValueError(
                f"R1 snapshot epoch budget mismatch: {saved_budget} != {epoch_budget}"
            )
        _replace_object_state(graph, restored["graph"])
        _replace_object_state(credit, restored["credit"])
        authority_payload = restored.get("r0_child_authority_payload")
        if r0_child_authority is not None:
            if not isinstance(authority_payload, bytes):
                raise RuntimeError("V2 R1 snapshot omitted child authority state")
            r0_child_authority = type(r0_child_authority).loads(
                authority_payload
            )
            if r0_child_authority.pending_event is not None:
                raise RuntimeError("restored V2 authority has a pending REAL event")
            persisted_seen = restored.get("v2_seen_predecessor_fens")
            if not isinstance(persisted_seen, tuple):
                raise RuntimeError("V2 R1 snapshot omitted its duplicate index")
            authoritative_seen = _v2_authoritative_predecessor_fens(
                r0_child_authority
            )
            if frozenset(persisted_seen) != authoritative_seen:
                raise RuntimeError(
                    "V2 R1 snapshot duplicate index differs from authority history"
                )
        elif authority_payload is not None:
            raise RuntimeError("legacy R1 arm snapshot contains V2 authority state")
        start_epoch = int(restored["next_epoch"])
        counters = dict(restored["counters"])
        reply_orbits = set(restored["reply_orbits"])
        reply_exposure_counts = dict(restored["reply_exposure_counts"])
        child_dispatch_cache = dict(restored["child_dispatch_cache"])
        checkpoints = list(restored["checkpoints"])
        composition_events = list(restored.get("composition_events", []))
        composition_consolidation_events = list(
            restored.get("composition_consolidation_events", [])
        )
        v2_structural_events = list(restored.get("v2_structural_events", []))
        history_snapshot_paths = list(restored.get("history_snapshot_paths", []))
        stopped_epoch = int(restored["stopped_epoch"])
        joint_mastery = bool(restored["joint_mastery"])
        duration_before_resume = float(restored["duration_seconds"])
        snapshot_writes = int(restored.get("snapshot_writes", 0))

    v2_seen_predecessor_fens = (
        set(_v2_authoritative_predecessor_fens(r0_child_authority))
        if r0_child_authority is not None
        else set()
    )

    evaluation_child_triplet_ids = (
        r0_child_triplet_ids if arm.mature_child_priority else None
    )
    evaluation_child_authority = (
        r0_child_authority if arm.mature_child_priority else None
    )
    evaluation_child_dispatch_cache = (
        child_dispatch_cache if config.freeze_r0_parameters_for_r1 else None
    )
    shuffled_schedule: tuple[bool, ...] = ()
    shuffled_schedule_audit: dict[str, Any] = {
        "enabled": False,
        "reason": "arm_does_not_shuffle_availability",
    }
    if arm.availability_mode == "shuffled_prototype_gate":
        shuffled_schedule, shuffled_schedule_audit = _shuffled_gate_schedule(
            graph,
            r0_gate,
            pools,
            r0_child_triplet_ids=r0_child_triplet_ids,
            epoch_budget=epoch_budget,
            seed=config.r1_shuffle_seed,
        )
        shuffled_schedule_audit = {
            "enabled": True,
            **shuffled_schedule_audit,
        }

    for epoch in range(start_epoch, epoch_budget):
        r0_frame_session = (
            None
            if (
                r0_child_authority is None
                or not callable(
                    getattr(r0_child_authority, "frame_session", None)
                )
            )
            else r0_child_authority.frame_session()
        )
        try:
            for position_index, fen in enumerate(pools.r1_train):
                board = chess.Board(fen)
                move, triplet_id, confirmed, graph_prediction = _scheduled_confirmed_action(
                    graph,
                    board,
                    schedule_index=epoch + position_index,
                    stage_diagnostic="R1_mate_in_2",
                )
                counters["formal_confirmation_failures"] += int(not confirmed)
                after_first = board.copy(stack=False)
                after_first.push(move)
                terminal_kind: str | None = _terminal_kind(after_first)
                successor_ids: tuple[str, ...] = ()
                if terminal_kind is None:
                    replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
                    if not replies:
                        terminal_kind = "failure"
                    else:
                        reply_key = (fen, move.uci())
                        reply_index = reply_exposure_counts.get(reply_key, 0)
                        reply = replies[reply_index % len(replies)]
                        reply_exposure_counts[reply_key] = reply_index + 1
                        successor = after_first.copy(stack=False)
                        successor.push(reply)
                        reply_orbits.add((fen, move.uci(), reply.uci()))
                        terminal_kind = _terminal_kind(successor)
                        if terminal_kind is None and r0_child_authority is not None:
                            available, response, duplicate, structural = (
                                _v2_r0_observe_training_successor(
                                    r0_child_authority,
                                    successor,
                                    seen_predecessor_fens=v2_seen_predecessor_fens,
                                    frame_id=(
                                        f"native-intrinsic-v2:{arm_name}:"
                                        f"{epoch}:{position_index}:"
                                        f"{move.uci()}:{reply.uci()}"
                                    ),
                                    frame_session=r0_frame_session,
                                )
                            )
                            counters["availability_queries"] += 1
                            counters["availability_positives"] += int(available)
                            counters["virtual_frame_queries"] += int(duplicate)
                            counters["v2_duplicate_virtual_queries"] += int(duplicate)
                            counters["v2_real_observations"] += int(not duplicate)
                            if structural is not None:
                                counters["v2_structural_transitions"] += 1
                                v2_structural_events.append(structural)
                                if r0_frame_session is not None:
                                    r0_frame_session.close()
                                    r0_frame_session = (
                                        r0_child_authority.frame_session()
                                    )
                            if arm.bootstrap_enabled and available:
                                successor_ids = (R0_COMPETENCE_ID,)
                                counters["child_handoffs"] += 1
                        elif terminal_kind is None and arm.bootstrap_enabled:
                            available, response, cache_hit, cache_mismatch = (
                                _r0_available_with_dispatch_cache(
                                    graph,
                                    r0_gate,
                                    successor,
                                    mode=arm.availability_mode,
                                    allowed_triplets=r0_child_triplet_ids,
                                    cache=child_dispatch_cache,
                                    enabled=config.freeze_r0_parameters_for_r1,
                                    cache_validation_mode=config.r0_child_cache_validation_mode,
                                )
                            )
                            counters["child_dispatch_cache_hits"] += int(cache_hit)
                            counters["child_dispatch_cache_misses"] += int(not cache_hit)
                            counters["child_dispatch_cache_mismatches"] += int(cache_mismatch)
                            counters["child_dispatch_cache_certified_hits"] += int(
                                response.get("cache_validation_mode") == "frozen_policy_token"
                            )
                            counters["virtual_frame_queries"] += int(
                                arm.availability_mode == "virtual_frame_verified"
                            )
                            if arm.availability_mode == "shuffled_prototype_gate":
                                schedule_index = counters["availability_queries"]
                                if schedule_index >= len(shuffled_schedule):
                                    raise RuntimeError("shuffled availability schedule exhausted")
                                available = shuffled_schedule[schedule_index]
                                response["availability_before_shuffle"] = bool(
                                    r0_gate.confirms(response["features"])
                                )
                                response["availability_after_shuffle"] = bool(available)
                            counters["availability_queries"] += 1
                            counters["availability_positives"] += int(available)
                            if available:
                                successor_ids = (R0_COMPETENCE_ID,)
                                counters["child_handoffs"] += 1
                credit.register(triplet_id, hierarchy_depth=1)
                credit.begin_episode()
                event = credit.transition(
                    triplet_id,
                    responsibilities=(
                        Responsibility(triplet_id, parent_distance=0),
                        Responsibility(R1_COMPETENCE_ID, parent_distance=1),
                    ),
                    successor_ids=successor_ids,
                    terminal_kind=terminal_kind,
                    prediction_override=graph_prediction,
                )
                counters["successor_value_sum"] += float(event.successor_value)
                graph.apply_intrinsic_td(
                    board,
                    move,
                    td_error=event.td_error,
                    stage_diagnostic="R1_mate_in_2",
                )
                counters["episodes"] += 1
                counters["failures"] += int(terminal_kind is not None)
        finally:
            if r0_frame_session is not None:
                r0_frame_session.close()

        replay = _replay_r0(
            graph,
            credit,
            pools.r0_train,
            epoch=epoch,
            count=config.r0_replay_per_r1_epoch,
            memory=r0_replay_memory,
        )
        counters["replay_episodes"] += replay["episodes"]
        counters["replay_mates"] += replay["observed_mates"]
        counters["replay_nonmates"] += replay["observed_nonmates"]
        counters["replay_confirmation_failures"] += replay["formal_confirmation_failures"]
        counters["replay_outcome_mismatches"] += replay["cached_outcome_mismatches"]
        counters["replay_seconds"] += replay["duration_seconds"]

        epoch_number = epoch + 1
        if (
            arm.composition_enabled
            and epoch_number in set(config.r1_composite_proposal_epochs)
        ):
            r1_triplet_ids = set(graph.triplet_ids).difference(r0_child_triplet_ids)
            proposals = graph.rank_shared_composite_candidates(
                r1_triplet_ids,
                max_candidates=config.r1_composite_max_candidates,
                max_atoms_per_triplet=config.r1_composite_max_atoms_per_triplet,
                min_support=config.r1_composite_min_support,
            )
            before_candidates = set(graph.composite_cells)
            for proposal in proposals:
                graph.materialize_shared_composite(
                    proposal["member_atom_ids"],
                    proposal["parent_triplet_ids"],
                    stage=f"R1_structural_epoch_{epoch_number}",
                )
            composition_events.append(
                {
                    "epoch": epoch_number,
                    "proposal_count": len(proposals),
                    "new_candidate_count": len(set(graph.composite_cells) - before_candidates),
                    "candidate_ids": [row["candidate_id"] for row in proposals],
                    "proposals": list(proposals),
                    "candidate_generation_used_outcome_label": False,
                    "candidate_generation_signal": "native_root_edge_weight",
                }
            )
        if (
            arm.composition_enabled
            and epoch_number in set(config.r1_composite_consolidation_epochs)
            and graph.composite_cells
        ):
            composition_consolidation_events.append(
                {
                    "epoch": epoch_number,
                    "pool_role": "training_only_paired_intervention",
                    "candidate_results": _paired_composite_interventions(
                        graph,
                        pools,
                        r0_child_triplet_ids=r0_child_triplet_ids,
                        child_dispatch_cache=child_dispatch_cache,
                        cycle=epoch_number,
                    ),
                }
            )
        ceiling_reason = (
            None
            if run_started is None
            else _development_ceiling_reason(config, run_started=run_started)
        )
        diagnostic_stop = (
            stop_after_epoch is not None and epoch_number >= stop_after_epoch
        )
        force_stop = diagnostic_stop or ceiling_reason is not None
        should_observe = (
            epoch == 0
            or epoch_number == epoch_budget
            or epoch_number % config.r1_validation_interval == 0
            or epoch_number % config.r1_snapshot_interval == 0
            or force_stop
        )
        latest_checkpoint: dict[str, Any] | None = None
        if ceiling_reason is not None:
            latest_checkpoint = {
                "epoch": epoch_number,
                "resource_ceiling_snapshot": True,
                "resource_ceiling_reason": ceiling_reason,
                "heldout_evaluation_skipped": True,
                "child_handoff_count": counters["child_handoffs"],
            }
            checkpoints.append(latest_checkpoint)
        elif should_observe:
            heldout_disabled_state = _disable_nonmature_composites(
                graph,
                enabled=config.r1_heldout_mature_composites_only,
            )
            metrics = _evaluate_r1(
                graph,
                pools.r1_validation,
                strata=pools.r1_validation_strata,
                max_samples=0,
                stop_after_first_failure=True,
                r0_child_triplet_ids=evaluation_child_triplet_ids,
                child_dispatch_cache=evaluation_child_dispatch_cache,
                r0_child_authority=evaluation_child_authority,
            )
            retention = _evaluate_r0(
                graph,
                pools.r0_regression,
                max_samples=0,
                r0_child_triplet_ids=evaluation_child_triplet_ids,
                child_dispatch_cache=evaluation_child_dispatch_cache,
                r0_child_authority=evaluation_child_authority,
            )
            latest_checkpoint = {
                "epoch": epoch_number,
                "validation_conversion_rate": metrics["conversion_rate"],
                "validation_stratum_conversion": metrics["stratum_conversion"],
                "child_handoff_count": counters["child_handoffs"],
                "r0_retention_accuracy": retention["accuracy"],
            }
            if (
                arm.bootstrap_enabled
                and metrics["conversion_rate"] >= config.r1_mastery_threshold
                and retention["accuracy"] >= config.r0_mastery_threshold
            ):
                regression_probe = _evaluate_r1(
                    graph,
                    pools.r1_regression,
                    strata=pools.r1_regression_strata,
                    max_samples=0,
                    stop_after_first_failure=True,
                    r0_child_triplet_ids=evaluation_child_triplet_ids,
                    child_dispatch_cache=evaluation_child_dispatch_cache,
                    r0_child_authority=evaluation_child_authority,
                )
                latest_checkpoint["regression_conversion_rate_at_mastery_probe"] = (
                    regression_probe["conversion_rate"]
                )
                latest_checkpoint["regression_stratum_conversion_at_mastery_probe"] = (
                    regression_probe["stratum_conversion"]
                )
                joint_mastery = bool(
                    regression_probe["conversion_rate"] >= config.r1_mastery_threshold
                )
                latest_checkpoint["joint_mastery"] = joint_mastery
                if joint_mastery:
                    stopped_epoch = epoch_number
            _restore_disabled_composites(graph, heldout_disabled_state)
            checkpoints.append(latest_checkpoint)

        should_snapshot = (
            epoch_number == epoch_budget
            or epoch_number % config.r1_snapshot_interval == 0
            or joint_mastery
            or force_stop
        )
        if should_snapshot:
            elapsed = duration_before_resume + (perf_counter() - started)
            if r0_child_authority is not None:
                authoritative_seen = _v2_authoritative_predecessor_fens(
                    r0_child_authority
                )
                if frozenset(v2_seen_predecessor_fens) != authoritative_seen:
                    raise RuntimeError(
                        "V2 duplicate index differs from authority history"
                    )
            authority_payload = (
                None
                if r0_child_authority is None
                else r0_child_authority.dumps()
            )
            history_path = _r1_history_snapshot_path(
                config, pools, arm_name, epoch_number
            )
            next_history_paths = list(history_snapshot_paths)
            if (
                config.r1_keep_checkpoint_history
                and str(history_path) not in next_history_paths
            ):
                next_history_paths.append(str(history_path))
            state = {
                "schema_version": "native_intrinsic_r1_arm_snapshot.v1",
                "fingerprint": fingerprint,
                "arm_name": arm_name,
                "arm_spec": asdict(arm),
                "source_identity": _source_identity(),
                "epoch_budget": epoch_budget,
                "next_epoch": epoch_number,
                "graph": graph,
                "credit": credit,
                "counters": counters,
                "reply_orbits": reply_orbits,
                "reply_exposure_counts": reply_exposure_counts,
                "child_dispatch_cache": child_dispatch_cache,
                "checkpoints": checkpoints,
                "composition_events": composition_events,
                "composition_consolidation_events": composition_consolidation_events,
                "v2_structural_events": v2_structural_events,
                "r0_child_authority_payload": authority_payload,
                "v2_seen_predecessor_fens": tuple(
                    sorted(v2_seen_predecessor_fens)
                ),
                "stopped_epoch": stopped_epoch,
                "joint_mastery": joint_mastery,
                "duration_seconds": elapsed,
                "snapshot_writes": snapshot_writes + 1,
                "history_snapshot_paths": next_history_paths,
            }
            _atomic_pickle(snapshot_path, state)
            if config.r1_keep_checkpoint_history:
                if history_path.exists():
                    existing = _load_r1_snapshot(
                        history_path, expected_fingerprint=fingerprint
                    )
                    if int(existing["next_epoch"]) != epoch_number:
                        raise RuntimeError("immutable history snapshot epoch mismatch")
                else:
                    _atomic_pickle(history_path, state)
                history_snapshot_paths = next_history_paths
            snapshot_writes += 1
            if latest_checkpoint is None:
                raise RuntimeError("R1 snapshot requires a current validation checkpoint")
            _write_live_r1_progress(
                config,
                arm_name=arm_name,
                epoch=epoch_number,
                checkpoint=latest_checkpoint,
                snapshot_path=snapshot_path,
                resumed=resumed_from_snapshot,
            )
        if force_stop:
            if ceiling_reason is not None:
                raise R1DevelopmentCeilingReached(
                    epoch=epoch_number,
                    snapshot_path=snapshot_path,
                    reason=ceiling_reason,
                )
            raise R1CheckpointInterrupt(
                epoch=epoch_number,
                snapshot_path=snapshot_path,
            )
        if joint_mastery:
            break

    duration_seconds = duration_before_resume + (perf_counter() - started)
    heldout_disabled_state = _disable_nonmature_composites(
        graph,
        enabled=config.r1_heldout_mature_composites_only,
    )
    final_validation = _evaluate_r1(
        graph,
        pools.r1_validation,
        strata=pools.r1_validation_strata,
        max_samples=config.max_samples,
        r0_child_triplet_ids=evaluation_child_triplet_ids,
        child_dispatch_cache=evaluation_child_dispatch_cache,
        r0_child_authority=evaluation_child_authority,
    )
    final_regression = _evaluate_r1(
        graph,
        pools.r1_regression,
        strata=pools.r1_regression_strata,
        max_samples=config.max_samples,
        r0_child_triplet_ids=evaluation_child_triplet_ids,
        child_dispatch_cache=evaluation_child_dispatch_cache,
        r0_child_authority=evaluation_child_authority,
    )
    final_r0_retention = _evaluate_r0(
        graph,
        pools.r0_regression,
        max_samples=config.max_samples,
        r0_child_triplet_ids=evaluation_child_triplet_ids,
        child_dispatch_cache=evaluation_child_dispatch_cache,
        r0_child_authority=evaluation_child_authority,
    )
    current_child_priority = bool(
        evaluation_child_triplet_ids is not None
        or evaluation_child_authority is not None
    )
    current_routing_name = (
        "child_priority_on" if current_child_priority else "child_priority_off"
    )
    routing_ablation: dict[str, Any] = {
        current_routing_name: {
            "validation": final_validation,
            "regression": final_regression,
            "reused_main_evaluation": True,
        }
    }
    alternate_routing_name = (
        "child_priority_off" if current_child_priority else "child_priority_on"
    )
    alternate_ids = (
        None if current_child_priority else r0_child_triplet_ids
    )
    alternate_authority = None if current_child_priority else r0_child_authority
    alternate_cache = child_dispatch_cache if alternate_ids is not None else None
    routing_ablation[alternate_routing_name] = {
        "validation": _evaluate_r1(
            graph,
            pools.r1_validation,
            strata=pools.r1_validation_strata,
            max_samples=0,
            r0_child_triplet_ids=alternate_ids,
            child_dispatch_cache=alternate_cache,
            r0_child_authority=alternate_authority,
        ),
        "regression": _evaluate_r1(
            graph,
            pools.r1_regression,
            strata=pools.r1_regression_strata,
            max_samples=0,
            r0_child_triplet_ids=alternate_ids,
            child_dispatch_cache=alternate_cache,
            r0_child_authority=alternate_authority,
        ),
        "reused_main_evaluation": False,
    }
    _restore_disabled_composites(graph, heldout_disabled_state)
    v2_authority_audit: dict[str, Any] = {
        "enabled": False,
        "reason": "arm_has_no_v2_child_authority",
    }
    if r0_child_authority is not None:
        authoritative_seen = _v2_authoritative_predecessor_fens(
            r0_child_authority
        )
        if frozenset(v2_seen_predecessor_fens) != authoritative_seen:
            raise RuntimeError("final V2 duplicate index differs from authority history")
        r0_child_authority.verify_full_history_boundary(
            f"native-intrinsic-r1-final:{arm_name}"
        )
        authority_payload = r0_child_authority.dumps()
        restored_authority = type(r0_child_authority).loads(authority_payload)
        if (
            restored_authority.continuation_manifest()
            != r0_child_authority.continuation_manifest()
        ):
            raise RuntimeError("final V2 child authority roundtrip mismatch")
        v2_authority_audit = {
            "enabled": True,
            "next_expected_ordinal": int(r0_child_authority.next_expected_ordinal),
            "discovery_event_count": len(r0_child_authority.base.receipts),
            "prospective_event_count": len(r0_child_authority.consumed_receipts),
            "current_generation": int(r0_child_authority.current_generation),
            "generation_phase": r0_child_authority.generation_phase.value,
            "candidate_count": len(r0_child_authority.states),
            "prospectively_certified_count": sum(
                state.prospectively_certified
                for state in r0_child_authority.states.values()
            ),
            "deferred_request_count": len(r0_child_authority.deferred_requests),
            "materialized_child_count": sum(
                birth.disposition == "MATERIALIZED"
                for birth in r0_child_authority.deferred_child_births.values()
            ),
            "continuation_digest": r0_child_authority.continuation_digest(),
            "seen_predecessor_count": len(authoritative_seen),
            "seen_predecessor_sha256": _hash_json(sorted(authoritative_seen)),
            "serialized_bytes": len(authority_payload),
            "serialized_sha256": hashlib.sha256(authority_payload).hexdigest(),
            "full_history_boundary_exact": True,
            "serialization_roundtrip_exact": True,
            "structural_events": v2_structural_events,
        }
    return {
        "training": {
            "episodes": counters["episodes"],
            "epoch_budget": epoch_budget,
            "stopped_epoch": stopped_epoch,
            "joint_mastery": joint_mastery,
            "duration_seconds": round(duration_seconds, 6),
            "resumed_from_snapshot": resumed_from_snapshot,
            "snapshot_path": str(snapshot_path),
            "snapshot_write_count": snapshot_writes,
            "history_snapshot_paths": history_snapshot_paths,
            "mechanistic_arm": asdict(arm),
            "child_value_control": child_value_control,
            "child_handoff_count": counters["child_handoffs"],
            "availability_query_count": counters["availability_queries"],
            "availability_positive_count": counters["availability_positives"],
            "availability_positive_rate": (
                0.0
                if counters["availability_queries"] == 0
                else counters["availability_positives"] / counters["availability_queries"]
            ),
            "shuffled_schedule": shuffled_schedule_audit,
            "successor_value_sum": counters["successor_value_sum"],
            "virtual_frame_query_count": counters["virtual_frame_queries"],
            "r0_replay_episode_count": counters["replay_episodes"],
            "r0_replay_mate_count": counters["replay_mates"],
            "r0_replay_nonmate_count": counters["replay_nonmates"],
            "r0_replay_formal_confirmation_failure_count": counters["replay_confirmation_failures"],
            "r0_replay_cached_outcome_mismatch_count": counters["replay_outcome_mismatches"],
            "r0_replay_duration_seconds": round(counters["replay_seconds"], 6),
            "r0_replay_mode": "memoized_mature_graph_response_live_confirmed",
            "r0_child_snapshot_triplet_count": len(r0_child_triplet_ids),
            "r0_child_dispatch_cache_entry_count": len(child_dispatch_cache),
            "r0_child_dispatch_cache_hit_count": counters["child_dispatch_cache_hits"],
            "r0_child_dispatch_cache_miss_count": counters["child_dispatch_cache_misses"],
            "r0_child_dispatch_cache_live_mismatch_count": counters["child_dispatch_cache_mismatches"],
            "r0_child_dispatch_cache_certified_hit_count": counters["child_dispatch_cache_certified_hits"],
            "r0_child_cache_validation_mode": config.r0_child_cache_validation_mode,
            "v2_real_observation_count": counters.get("v2_real_observations", 0),
            "v2_duplicate_virtual_query_count": counters.get(
                "v2_duplicate_virtual_queries", 0
            ),
            "v2_structural_transition_count": counters.get(
                "v2_structural_transitions", 0
            ),
            "v2_availability_used_for_bootstrap": bool(arm.bootstrap_enabled),
            "v2_same_event_outcome_used_for_bootstrap": False,
            "observed_terminal_failure_count": counters["failures"],
            "unique_first_move_reply_exposures": len(reply_orbits),
            "distinct_first_move_actions_exposed": len(reply_exposure_counts),
            "reply_schedule": "per_position_action_content_blind_round_robin",
            "formal_confirmation_failure_count": counters["formal_confirmation_failures"],
            "teacher_positive_move_sets_consumed": 0,
            "forced_first_move_labels_consumed": 0,
            "validation_checkpoints": checkpoints,
            "composition_proposal_epochs": list(config.r1_composite_proposal_epochs),
            "composition_events": composition_events,
            "composition_consolidation_epochs": list(
                config.r1_composite_consolidation_epochs
            ),
            "composition_consolidation_events": composition_consolidation_events,
            "composite_candidate_count": len(graph.composite_cells),
            "composite_mature_count": sum(
                cell.state.name == "MATURE" for cell in graph.composite_cells.values()
            ),
            "composite_causal_intervention_count": sum(
                cell.candidate_stats.credit_stats.total_interventions
                for cell in graph.composite_cells.values()
            ),
            "heldout_mature_composites_only": config.r1_heldout_mature_composites_only,
        },
        "validation": final_validation,
        "regression": final_regression,
        "routing_ablation": routing_ablation,
        "r0_retention": final_r0_retention,
        "graph": graph.learned_state_audit(),
        "credit": credit.snapshot(),
        "v2_child_authority": v2_authority_audit,
    }

def _disable_nonmature_composites(
    graph: NativeReConKRKGraph,
    *,
    enabled: bool,
) -> set[str] | None:
    if not enabled:
        return None
    original = set(graph.disabled_composite_ids)
    graph.disabled_composite_ids.update(
        composite_id
        for composite_id, cell in graph.composite_cells.items()
        if cell.state != StemCellState.MATURE
    )
    return original


def _restore_disabled_composites(
    graph: NativeReConKRKGraph,
    state: set[str] | None,
) -> None:
    if state is None:
        return
    graph.disabled_composite_ids.clear()
    graph.disabled_composite_ids.update(state)


def _paired_composite_interventions(
    graph: NativeReConKRKGraph,
    pools: _Pools,
    *,
    r0_child_triplet_ids: frozenset[str],
    child_dispatch_cache: dict[str, dict[str, Any]],
    cycle: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for composite_id in sorted(graph.composite_cells):
        cell = graph.composite_cells[composite_id]
        if cell.state != StemCellState.TRIAL:
            continue
        was_enabled = composite_id not in graph.disabled_composite_ids
        graph.set_composite_enabled(composite_id, enabled=True)
        enabled = _evaluate_r1(
            graph,
            pools.r1_train,
            strata=pools.r1_train_strata,
            max_samples=len(pools.r1_train),
            r0_child_triplet_ids=r0_child_triplet_ids,
            child_dispatch_cache=child_dispatch_cache,
        )
        graph.set_composite_enabled(composite_id, enabled=False)
        disabled = _evaluate_r1(
            graph,
            pools.r1_train,
            strata=pools.r1_train_strata,
            max_samples=len(pools.r1_train),
            r0_child_triplet_ids=r0_child_triplet_ids,
            child_dispatch_cache=child_dispatch_cache,
        )
        graph.set_composite_enabled(composite_id, enabled=was_enabled)
        help_count = hurt_count = neutral_count = 0
        for enabled_row, disabled_row in zip(
            enabled["samples"],
            disabled["samples"],
            strict=True,
        ):
            enabled_return = float(bool(enabled_row["all_replies_mated"]))
            disabled_return = float(bool(disabled_row["all_replies_mated"]))
            graph.record_composite_intervention(
                composite_id,
                enabled_return=enabled_return,
                disabled_return=disabled_return,
                cycle=cycle,
            )
            help_count += int(enabled_return > disabled_return)
            hurt_count += int(enabled_return < disabled_return)
            neutral_count += int(enabled_return == disabled_return)
        consolidation = graph.consolidate_composite_candidate(composite_id)
        results.append(
            {
                "composite_id": composite_id,
                "enabled_conversion_rate": enabled["conversion_rate"],
                "disabled_conversion_rate": disabled["conversion_rate"],
                "paired_help_count": help_count,
                "paired_hurt_count": hurt_count,
                "paired_neutral_count": neutral_count,
                "outcome_source": "real_chess_world_training_pool_conversion",
                "recognizer_verdict_used_for_credit": False,
                "consolidation": consolidation,
            }
        )
    return results


def _replay_r0(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    fens: Sequence[str],
    *,
    epoch: int,
    count: int,
    memory: Sequence[_R0ReplayExperience] | None = None,
) -> dict[str, Any]:
    episodes = observed_mates = observed_nonmates = 0
    confirmation_failures = outcome_mismatches = 0
    started = perf_counter()
    if (not fens and not memory) or count <= 0:
        return {
            "episodes": 0,
            "observed_mates": 0,
            "observed_nonmates": 0,
            "formal_confirmation_failures": 0,
            "cached_outcome_mismatches": 0,
            "duration_seconds": 0.0,
        }
    for replay_index in range(count):
        experience = (
            memory[(epoch * count + replay_index) % len(memory)]
            if memory
            else None
        )
        fen = (
            experience.fen
            if experience is not None
            else fens[(epoch * count + replay_index) % len(fens)]
        )
        board = chess.Board(fen)
        audit = (
            graph.confirm_candidate(
                board,
                triplet_id=experience.triplet_id,
                move_uci=experience.move_uci,
            )
            if experience is not None
            else graph.audit_choice(board)
        )
        selected = audit.get("selected_move")
        graph_prediction = float(audit.get("selected_score_raw") or 0.0)
        if selected is None:
            confirmation_failures += 1
            continue
        move = chess.Move.from_uci(str(selected))
        if move not in board.legal_moves:
            confirmation_failures += 1
            continue
        triplet_id = graph.ensure_triplet(
            board,
            move,
            stage="R0_outcome_replay",
        )
        terminal_kind = _execute_white_and_observe(board, move)
        if experience is not None:
            outcome_mismatches += int(terminal_kind != experience.observed_terminal)
        credit.register(triplet_id, hierarchy_depth=1)
        credit.begin_episode()
        event = credit.transition(
            triplet_id,
            responsibilities=(
                Responsibility(triplet_id, parent_distance=0),
                Responsibility(R0_COMPETENCE_ID, parent_distance=1),
            ),
            terminal_kind=terminal_kind,
            prediction_override=graph_prediction,
        )
        graph.apply_intrinsic_td(
            board,
            move,
            td_error=event.td_error,
            stage_diagnostic="R0_outcome_replay",
        )
        episodes += 1
        observed_mates += int(terminal_kind == "mate")
        observed_nonmates += int(terminal_kind != "mate")
    return {
        "episodes": episodes,
        "observed_mates": observed_mates,
        "observed_nonmates": observed_nonmates,
        "formal_confirmation_failures": confirmation_failures,
        "cached_outcome_mismatches": outcome_mismatches,
        "duration_seconds": round(perf_counter() - started, 6),
    }


def _build_r0_replay_memory(
    graph: NativeReConKRKGraph,
    fens: Sequence[str],
) -> tuple[tuple[_R0ReplayExperience, ...], dict[str, Any]]:
    """Memoize mature graph responses without importing solution labels."""

    started = perf_counter()
    experiences: list[_R0ReplayExperience] = []
    null_responses = illegal_responses = 0
    for fen in fens:
        board = chess.Board(fen)
        audit = graph.audit_choice(board)
        move_uci = audit.get("selected_move")
        triplet_id = audit.get("selected_triplet")
        if move_uci is None or triplet_id is None:
            null_responses += 1
            continue
        move = chess.Move.from_uci(str(move_uci))
        if move not in board.legal_moves:
            illegal_responses += 1
            continue
        experiences.append(
            _R0ReplayExperience(
                fen=fen,
                move_uci=move.uci(),
                triplet_id=str(triplet_id),
                observed_terminal=_execute_white_and_observe(board, move),
            )
        )
    rows = [asdict(item) for item in experiences]
    return tuple(experiences), {
        "source": "mature_r0_graph_selected_responses",
        "cache_used_as_move_provider": False,
        "live_formal_reconfirmation_required": True,
        "world_outcome_reexecuted_on_every_replay": True,
        "teacher_solution_labels_consumed": 0,
        "requested_position_count": len(fens),
        "experience_count": len(experiences),
        "null_response_count": null_responses,
        "illegal_response_count": illegal_responses,
        "mate_experience_count": sum(
            item.observed_terminal == "mate" for item in experiences
        ),
        "manifest_sha256": _hash_json(rows),
        "build_duration_seconds": round(perf_counter() - started, 6),
        "experiences": rows,
    }


def _arm_progress_summary(arm: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "training_episodes": arm["training"]["episodes"],
        "stopped_epoch": arm["training"]["stopped_epoch"],
        "joint_mastery": arm["training"]["joint_mastery"],
        "child_handoff_count": arm["training"]["child_handoff_count"],
        "r0_replay_episode_count": arm["training"]["r0_replay_episode_count"],
        "validation_conversion_rate": arm["validation"]["conversion_rate"],
        "regression_conversion_rate": arm["regression"]["conversion_rate"],
        "r0_retention_accuracy": arm["r0_retention"]["accuracy"],
    }


def _scheduled_confirmed_action(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    *,
    schedule_index: int,
    stage_diagnostic: str,
) -> tuple[chess.Move, str, bool, float]:
    legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    if not legal:
        raise ValueError("training position has no legal action")
    move = legal[int(schedule_index) % len(legal)]
    triplet_id = graph.ensure_triplet(board, move, stage=stage_diagnostic)
    audit = graph.confirm_candidate(
        board,
        triplet_id=triplet_id,
        move_uci=move.uci(),
    )
    confirmed = audit.get("selected_move") == move.uci()
    graph_prediction = float(audit.get("selected_score_raw") or 0.0)
    return move, triplet_id, bool(confirmed), graph_prediction


def _execute_white_and_observe(board: chess.Board, move: chess.Move) -> str | None:
    if move not in board.legal_moves:
        return "illegal"
    after = board.copy(stack=False)
    after.push(move)
    return _terminal_kind(after)


def _terminal_kind(board: chess.Board) -> str | None:
    if board.is_checkmate():
        return "mate"
    if board.is_stalemate():
        return "stalemate"
    if not board.pieces(chess.ROOK, chess.WHITE):
        return "rook_loss"
    return None


def _choose_with_child_priority(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    *,
    r0_child_triplet_ids: frozenset[str] | None,
    child_dispatch_cache: dict[str, dict[str, Any]] | None = None,
    r0_child_authority: Any | None = None,
) -> chess.Move | None:
    """Let a mature child control only when its own virtual reply is available."""

    if r0_child_authority is not None:
        available, response = _v2_r0_available(
            r0_child_authority,
            board,
            frame_id=(
                "native-intrinsic-v2-evaluation:"
                + hashlib.sha256(board.fen().encode("utf-8")).hexdigest()
            ),
        )
        selected_uci = response.get("selected_move")
        if available and selected_uci is not None:
            move = chess.Move.from_uci(str(selected_uci))
            if move in board.legal_moves:
                return move
    elif r0_child_triplet_ids:
        if child_dispatch_cache is None:
            available, response = _r0_available(
                graph,
                None,
                board,
                mode="virtual_frame_verified",
                allowed_triplets=r0_child_triplet_ids,
            )
        else:
            available, response, _cache_hit, _cache_mismatch = (
                _r0_available_with_dispatch_cache(
                    graph,
                    None,
                    board,
                    mode="virtual_frame_verified",
                    allowed_triplets=r0_child_triplet_ids,
                    cache=child_dispatch_cache,
                    enabled=True,
                )
            )
        selected_uci = response.get("selected_move")
        if available and selected_uci is not None:
            move = chess.Move.from_uci(str(selected_uci))
            if move in board.legal_moves:
                return move
    return graph.choose(board)


def _evaluate_r0(
    graph: NativeReConKRKGraph,
    fens: Sequence[str],
    *,
    masked_triplets: set[str] | None = None,
    max_samples: int,
    r0_child_triplet_ids: frozenset[str] | None = None,
    child_dispatch_cache: dict[str, dict[str, Any]] | None = None,
    r0_child_authority: Any | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = illegal = null = stalemate = rook_loss = 0
    for fen in fens:
        board = chess.Board(fen)
        move = (
            _choose_with_child_priority(
                graph,
                board,
                r0_child_triplet_ids=r0_child_triplet_ids,
                child_dispatch_cache=child_dispatch_cache,
                r0_child_authority=r0_child_authority,
            )
            if (r0_child_triplet_ids or r0_child_authority is not None)
            and not masked_triplets
            else graph.choose(board, masked_triplets=masked_triplets)
        )
        terminal_kind = None if move is None else _execute_white_and_observe(board, move)
        ok = terminal_kind == "mate"
        correct += int(ok)
        null += int(move is None)
        illegal += int(move is not None and move not in board.legal_moves)
        stalemate += int(terminal_kind == "stalemate")
        rook_loss += int(terminal_kind == "rook_loss")
        if len(rows) < max_samples:
            rows.append(
                {
                    "fen": fen,
                    "selected_move": None if move is None else move.uci(),
                    "observed_terminal": terminal_kind,
                    "correct": ok,
                }
            )
    total = len(fens)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "null_selection_count": null,
        "illegal_move_count": illegal,
        "stalemate_count": stalemate,
        "rook_loss_count": rook_loss,
        "samples": rows,
    }


@lru_cache(maxsize=8192)
def _diagnostic_forced_first_uci(fen: str) -> frozenset[str]:
    """Cache laboratory-only Mate-in-2 labels across repeated arm evaluation."""

    board = chess.Board(fen)
    return frozenset(move.uci() for move in _forced_mate_in_two_first_moves(board))


def _evaluate_r1(
    graph: NativeReConKRKGraph,
    fens: Sequence[str],
    *,
    max_samples: int,
    strata: Sequence[str] | None = None,
    stop_after_first_failure: bool = False,
    r0_child_triplet_ids: frozenset[str] | None = None,
    child_dispatch_cache: dict[str, dict[str, Any]] | None = None,
    r0_child_authority: Any | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    converted = parent_correct = null = illegal = reply_total = reply_mated = 0
    if strata is not None and len(strata) != len(fens):
        raise ValueError("R1 evaluation FEN and stratum sequences must align")
    stratum_conversion: dict[str, dict[str, int | float]] = {}
    for position_index, fen in enumerate(fens):
        stratum = "unstratified" if strata is None else str(strata[position_index])
        board = chess.Board(fen)
        first = _choose_with_child_priority(
            graph,
            board,
            r0_child_triplet_ids=r0_child_triplet_ids,
            child_dispatch_cache=child_dispatch_cache,
            r0_child_authority=r0_child_authority,
        )
        forced_first_uci = _diagnostic_forced_first_uci(fen)
        first_is_parent_correct = bool(
            first is not None and first.uci() in forced_first_uci
        )
        parent_correct += int(first_is_parent_correct)
        null += int(first is None)
        illegal += int(first is not None and first not in board.legal_moves)
        all_replies_mated = False
        reply_rows: list[dict[str, Any]] = []
        if first is not None and first in board.legal_moves:
            after_first = board.copy(stack=False)
            after_first.push(first)
            replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
            all_replies_mated = bool(replies)
            for reply in replies:
                before_second = after_first.copy(stack=False)
                before_second.push(reply)
                second = _choose_with_child_priority(
                    graph,
                    before_second,
                    r0_child_triplet_ids=r0_child_triplet_ids,
                    child_dispatch_cache=child_dispatch_cache,
                    r0_child_authority=r0_child_authority,
                )
                terminal_kind = (
                    None
                    if second is None
                    else _execute_white_and_observe(before_second, second)
                )
                ok = terminal_kind == "mate"
                reply_total += 1
                reply_mated += int(ok)
                all_replies_mated = all_replies_mated and ok
                if len(reply_rows) < 8:
                    reply_rows.append(
                        {
                            "reply": reply.uci(),
                            "second": None if second is None else second.uci(),
                            "observed_terminal": terminal_kind,
                            "mated": ok,
                        }
                    )
                if stop_after_first_failure and not ok:
                    break
        converted += int(all_replies_mated)
        stratum_row = stratum_conversion.setdefault(
            stratum,
            {
                "position_count": 0,
                "conversion_count": 0,
                "conversion_rate": 0.0,
            },
        )
        stratum_row["position_count"] = int(stratum_row["position_count"]) + 1
        stratum_row["conversion_count"] = (
            int(stratum_row["conversion_count"]) + int(all_replies_mated)
        )
        if len(rows) < max_samples:
            rows.append(
                {
                    "fen": fen,
                    "stratum": stratum,
                    "selected_first": None if first is None else first.uci(),
                    "parent_first_move_correct": first_is_parent_correct,
                    "all_replies_mated": all_replies_mated,
                    "reply_checks": reply_rows,
                }
            )
    total = len(fens)
    for values in stratum_conversion.values():
        position_count = int(values["position_count"])
        values["conversion_rate"] = (
            0.0
            if position_count == 0
            else int(values["conversion_count"]) / position_count
        )
    return {
        "position_count": total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "parent_first_move_correct_count": parent_correct,
        "parent_first_move_correct_rate": 0.0 if total == 0 else parent_correct / total,
        "parent_correctness_label_role": "trainer_side_diagnostic_only",
        "reply_mate_rate": 0.0 if reply_total == 0 else reply_mated / reply_total,
        "reply_evaluation_count": reply_total,
        "null_selection_count": null,
        "illegal_move_count": illegal,
        "reply_evaluation_mode": (
            "early_exit_on_failure" if stop_after_first_failure else "exhaustive"
        ),
        "mature_child_priority_enabled": bool(
            r0_child_triplet_ids or r0_child_authority is not None
        ),
        "stratum_conversion": dict(sorted(stratum_conversion.items())),
        "samples": rows,
    }


def _fit_r0_gate(
    graph: NativeReConKRKGraph,
    *,
    train_positive: Sequence[str],
    train_negative: Sequence[str],
    validation_positive: Sequence[str],
    validation_negative: Sequence[str],
    regression_positive: Sequence[str],
    regression_negative: Sequence[str],
) -> tuple[OutcomeCalibratedPrototypeGate, dict[str, Any]]:
    train = [_gate_example(graph, fen) for fen in (*train_positive, *train_negative)]
    validation = [
        _gate_example(graph, fen)
        for fen in (*validation_positive, *validation_negative)
    ]
    regression = [
        _gate_example(graph, fen)
        for fen in (*regression_positive, *regression_negative)
    ]
    candidates: list[OutcomeCalibratedPrototypeGate] = []
    candidate_rows: list[dict[str, Any]] = []
    for neighbors in (1, 3, 5, 7):
        for threshold in (0.25, 0.40, 0.50, 0.60, 0.75):
            gate = OutcomeCalibratedPrototypeGate.fit(
                GATE_FEATURE_NAMES,
                train,
                validation,
                PrototypeCompetenceGateConfig(
                    neighbors=neighbors,
                    threshold=threshold,
                    min_validation_true_positives=len(validation_positive),
                    max_validation_false_positives=0,
                    min_validation_precision=1.0,
                ),
            )
            candidates.append(gate)
            candidate_rows.append(
                {
                    "neighbors": neighbors,
                    "threshold": threshold,
                    "validation_metrics": dict(gate.validation_metrics),
                }
            )
    selected = max(
        candidates,
        key=lambda gate: (
            int(gate.validation_metrics["false_positive"] == 0),
            int(gate.validation_metrics["true_positive"]),
            -int(gate.validation_metrics["false_positive"]),
            float(gate.validation_metrics["precision"]),
            -abs(float(gate.threshold) - 0.5),
            -int(gate.neighbors),
        ),
    )
    regression_metrics = selected.evaluate(regression)
    regression_pass = bool(
        regression_metrics["true_positive"] == len(regression_positive)
        and regression_metrics["false_positive"] == 0
    )
    selected.mature = bool(selected.mature and regression_pass)
    selection = {
        "selection_split": "gate_validation",
        "confirmation_split": "gate_regression",
        "candidate_count": len(candidate_rows),
        "candidates": candidate_rows,
        "selected_neighbors": selected.neighbors,
        "selected_threshold": selected.threshold,
        "selected_validation_metrics": dict(selected.validation_metrics),
        "regression_metrics": regression_metrics,
        "regression_positive_count": len(regression_positive),
        "regression_negative_count": len(regression_negative),
        "joint_gate_certification_pass": selected.mature,
    }
    return selected, selection


def _gate_example(graph: NativeReConKRKGraph, fen: str) -> CompetenceGateExample:
    board = chess.Board(fen)
    response = _policy_response(graph, board)
    return CompetenceGateExample(
        features=response["features"],
        success=bool(response["observed_immediate_mate"]),
    )


def _v2_r0_available(
    authority: Any,
    board: chess.Board,
    *,
    frame_id: str,
    frame_session: Any | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Query only the V2 graph-emitted availability capability."""

    before = str(
        authority.continuation_digest()
        if frame_session is None
        else frame_session.continuation_digest(authority)
    )
    frame = FrameContext(
        frame_id=str(frame_id),
        kind=FrameKind.VIRTUAL,
        values={"board": board.copy(stack=False)},
    )
    opened = (
        authority.open_virtual(frame)
        if frame_session is None
        else authority.open_virtual(
            frame, frame_session=frame_session
        )
    )
    query = opened.get("query")
    if query is None:
        raise RuntimeError("V2 child authority omitted its graph query")
    provenance = dict(query.availability_provenance or {})
    if provenance.get("authority") != "NativeProspectiveAuthorityV2_graph_emission":
        raise RuntimeError("V2 child availability bypassed graph authority")
    if int(provenance.get("certification_evidence_added", -1)) != 0:
        raise RuntimeError("VIRTUAL V2 query created certification evidence")
    after = str(
        authority.continuation_digest()
        if frame_session is None
        else frame_session.continuation_digest(authority)
    )
    if after != before:
        raise RuntimeError("VIRTUAL V2 query mutated the persistent authority")
    actuation = query.actuation
    selected_move = None if actuation is None else str(actuation.move_uci)
    response = {
        "selected_move": selected_move,
        "selected_triplet": (
            None if actuation is None else str(actuation.option_identity)
        ),
        "observed_immediate_mate": bool(query.response.available),
        "availability_source": "v2_prospective_graph_emission",
        "availability_provenance": provenance,
        "classification": opened["classification"].to_manifest(),
        "virtual_frame_terminal_grounding_granted": False,
    }
    return bool(query.response.available), response


def _advance_v2_structural_frontier(authority: Any) -> dict[str, Any] | None:
    schedule = tuple(int(item) for item in authority.structural_epoch_schedule)
    generation = int(authority.current_generation)
    if generation >= len(schedule):
        return None
    if int(authority.next_expected_ordinal) != schedule[generation]:
        return None
    sealed = authority.seal_prospective_generation()
    structural = authority.open_structural_successor()
    consumptions: list[dict[str, Any]] = []
    child_ids: list[str] = []
    while any(
        request_id not in authority.request_consumptions
        for request_id in authority.sealed_request_ids
    ):
        consumption = authority.consume_next_structural_request()
        row = consumption.manifest()
        if consumption.child_cell_id is not None:
            child_id = authority.materialize_deferred_child(
                consumption.request_id
            )
            child_ids.append(child_id)
            row = {**row, "materialized_child_id": child_id}
        consumptions.append(row)
    prospective = authority.open_prospective_successor()
    return {
        "sealed_boundary": sealed.manifest(),
        "structural_boundary": structural.manifest(),
        "prospective_boundary": prospective.manifest(),
        "sealed_request_count": len(authority.sealed_request_ids),
        "consumptions": consumptions,
        "child_ids": child_ids,
    }


def _v2_authoritative_predecessor_fens(authority: Any) -> frozenset[str]:
    """Rebuild the duplicate index only from signed/accepted authority history."""

    discovery = {
        str(item.predecessor_fen) for item in authority.base.receipts.values()
    }
    prospective = {
        str(item.predecessor_fen)
        for item in authority.consumed_receipts.values()
    }
    return frozenset(discovery | prospective)


def _v2_r0_observe_training_successor(
    authority: Any,
    board: chess.Board,
    *,
    seen_predecessor_fens: set[str],
    frame_id: str,
    frame_session: Any | None = None,
) -> tuple[bool, dict[str, Any], bool, dict[str, Any] | None]:
    """Classify before one unique REAL result, then learn for later events."""

    predecessor_fen = board.fen()
    if predecessor_fen in seen_predecessor_fens:
        available, response = _v2_r0_available(
            authority,
            board,
            frame_id=f"{frame_id}:duplicate-virtual",
            frame_session=frame_session,
        )
        return available, response, True, None

    frame = FrameContext(
        frame_id=str(frame_id),
        kind=FrameKind.REAL,
        values={"board": board.copy(stack=False)},
    )
    pending, trace = (
        authority.open_real_event(frame)
        if frame_session is None
        else authority.open_real_event(
            frame, frame_session=frame_session
        )
    )
    selected_move = chess.Move.from_uci(trace.actuation.move_uci)
    successor = board.copy(stack=False)
    successor.push(selected_move)
    receipt = authority.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=board,
        successor=successor,
    )
    emission = (
        authority.consume(receipt)
        if frame_session is None
        else authority.consume(receipt, frame_session=frame_session)
    )
    seen_predecessor_fens.add(predecessor_fen)
    classification = pending.pre_outcome_classification.to_manifest()
    available = str(classification["state"]).lower() == "available"
    response = {
        "selected_move": selected_move.uci(),
        "selected_triplet": str(trace.actuation.option_identity),
        "observed_immediate_mate": successor.is_checkmate(),
        "availability_source": "v2_prospective_pre_outcome_graph_emission",
        "classification": classification,
        "certification_emission": emission.manifest(),
        "virtual_frame_terminal_grounding_granted": False,
    }
    structural = _advance_v2_structural_frontier(authority)
    return available, response, False, structural


def _r0_available(
    graph: NativeReConKRKGraph,
    gate: OutcomeCalibratedPrototypeGate | None,
    board: chess.Board,
    *,
    mode: str = "prototype_gate",
    allowed_triplets: Iterable[str] | None = None,
) -> tuple[bool, dict[str, Any]]:
    normalized = str(mode).strip().lower()
    if normalized in {"prototype_gate", "shuffled_prototype_gate"}:
        if gate is None:
            raise ValueError("prototype_gate mode requires a fitted gate")
        response = _policy_response(
            graph,
            board,
            observe_outcome=False,
            allowed_triplets=allowed_triplets,
        )
        response["availability_source"] = (
            "outcome_calibrated_prototype_gate"
            if normalized == "prototype_gate"
            else "prototype_gate_before_rate_matched_shuffle"
        )
        return bool(gate.confirms(response["features"])), response
    if normalized == "virtual_frame_verified":
        response = _policy_response(
            graph,
            board,
            observe_outcome=True,
            allowed_triplets=allowed_triplets,
        )
        response["availability_source"] = "mature_child_selected_virtual_frame"
        response["virtual_frame_terminal_grounding_granted"] = False
        return bool(response["observed_immediate_mate"]), response
    raise ValueError(
        "r0_availability_mode must be prototype_gate, shuffled_prototype_gate, "
        "virtual_frame_verified, or v2_prospective"
    )


def _r0_available_with_dispatch_cache(
    graph: NativeReConKRKGraph,
    gate: OutcomeCalibratedPrototypeGate | None,
    board: chess.Board,
    *,
    mode: str,
    allowed_triplets: frozenset[str],
    cache: dict[str, dict[str, Any]],
    enabled: bool,
    cache_validation_mode: str = "live_formal",
) -> tuple[bool, dict[str, Any], bool, bool]:
    """Memoize a frozen child response with formal or policy-token validation."""

    validation_mode = str(cache_validation_mode).strip().lower()
    if validation_mode not in {"live_formal", "frozen_policy_token"}:
        raise ValueError(
            "r0_child_cache_validation_mode must be live_formal or frozen_policy_token"
        )
    if not enabled or str(mode).strip().lower() != "virtual_frame_verified":
        available, response = _r0_available(
            graph,
            gate,
            board,
            mode=mode,
            allowed_triplets=allowed_triplets,
        )
        return available, response, False, False

    cache_key = board.fen()
    entry = cache.get(cache_key)
    if entry is not None:
        selected_uci: str | None = None
        selected_triplet: str | None = None
        source = "live_confirmed_frozen_child_dispatch_memory"
        used_validation_mode = "live_formal"
        if validation_mode == "frozen_policy_token":
            expected_token = entry.get("frozen_policy_token")
            current_token = graph.frozen_child_policy_token(allowed_triplets)
            cached_move = str(entry["move_uci"])
            cached_triplet = str(entry["triplet_id"])
            move = chess.Move.from_uci(cached_move)
            if (
                expected_token is not None
                and current_token == expected_token
                and cached_triplet in allowed_triplets
                and move in board.legal_moves
            ):
                selected_uci = cached_move
                selected_triplet = cached_triplet
                source = "frozen_policy_token_certified_child_dispatch_memory"
                used_validation_mode = "frozen_policy_token"
        if selected_uci is None:
            confirmation = graph.confirm_candidate(
                board,
                triplet_id=str(entry["triplet_id"]),
                move_uci=str(entry["move_uci"]),
            )
            selected_uci = confirmation.get("selected_move")
            selected_triplet = confirmation.get("selected_triplet")
        observed_mate = False
        if selected_uci is not None:
            move = chess.Move.from_uci(str(selected_uci))
            observed_mate = _execute_white_and_observe(board, move) == "mate"
        response = {
            "selected_move": selected_uci,
            "selected_triplet": selected_triplet,
            "observed_immediate_mate": observed_mate,
            "availability_source": source,
            "cache_validation_mode": used_validation_mode,
            "virtual_frame_terminal_grounding_granted": False,
        }
        available = bool(observed_mate)
        return available, response, True, available != bool(entry["available"])

    available, response = _r0_available(
        graph,
        gate,
        board,
        mode=mode,
        allowed_triplets=allowed_triplets,
    )
    selected_move = response.get("selected_move")
    selected_triplet = response.get("selected_triplet")
    if selected_move is not None and selected_triplet is not None:
        cache[cache_key] = {
            "move_uci": str(selected_move),
            "triplet_id": str(selected_triplet),
            "available": bool(available),
            "frozen_policy_token": graph.frozen_child_policy_token(allowed_triplets),
        }
    response["cache_validation_mode"] = "live_formal"
    return available, response, False, False

def _policy_response(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    *,
    observe_outcome: bool = True,
    allowed_triplets: Iterable[str] | None = None,
) -> dict[str, Any]:
    masked_triplets = (
        None
        if allowed_triplets is None
        else graph.triplet_ids.difference(set(allowed_triplets))
    )
    audit = graph.audit_choice(board, masked_triplets=masked_triplets)
    candidates = list(audit.get("confirmed_candidates", ()))
    selected_score = float(audit.get("selected_score") or 0.0)
    runner_up = float(candidates[1]["score"]) if len(candidates) > 1 else 0.0
    scores = [float(row["score"]) for row in candidates]
    top4 = scores[:4]
    top16 = scores[:16]
    top4_mean, top4_std = _mean_std(top4)
    top16_mean, top16_std = _mean_std(top16)
    score_range = 0.0 if not scores else scores[0] - scores[-1]
    margin = selected_score - runner_up
    selected_uci = audit.get("selected_move")
    observed_mate = False
    if observe_outcome and selected_uci is not None:
        move = chess.Move.from_uci(str(selected_uci))
        observed_mate = _execute_white_and_observe(board, move) == "mate"
    return {
        "features": (
            selected_score,
            margin,
            float(audit.get("confirmed_candidate_count", 0)),
            float(audit.get("candidate_triplet_count", 0)),
            top4_mean,
            top4_std,
            top16_mean,
            top16_std,
            score_range,
            selected_score * selected_score,
            margin * margin,
            selected_score * margin,
            float(len({str(row["move"]) for row in candidates[:16]})),
            float(len({str(row["triplet_id"]) for row in candidates[:16]})),
        ),
        "selected_move": selected_uci,
        "selected_triplet": audit.get("selected_triplet"),
        "observed_immediate_mate": observed_mate,
    }


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return mean, variance**0.5


def _clone_parity(
    graph: NativeReConKRKGraph,
    probe_fens: Sequence[str],
) -> dict[str, Any]:
    clone = copy.deepcopy(graph)
    original = [
        None if (move := graph.choose(chess.Board(fen))) is None else move.uci()
        for fen in probe_fens[:8]
    ]
    restored = [
        None if (move := clone.choose(chess.Board(fen))) is None else move.uci()
        for fen in probe_fens[:8]
    ]
    return {
        "mechanism": "in_memory_deepcopy_preliminary_probe",
        "serialized_snapshot_resume_implemented": False,
        "probe_count": len(original),
        "choices_equal": original == restored,
        "original_choices": original,
        "clone_choices": restored,
    }


def _generate_non_m1_positions(
    *,
    count: int,
    seed: int,
    excluded: set[str],
    max_attempts: int,
) -> tuple[str, ...]:
    rng = random.Random(seed)
    used = set(excluded)
    rows: list[str] = []
    for _ in range(max_attempts):
        if len(rows) >= count:
            break
        board = _random_krk_board(rng)
        fen = board.fen()
        if fen in used or not _valid_foundation_board(board):
            continue
        if _has_immediate_mate(board):
            continue
        used.add(fen)
        rows.append(fen)
    if len(rows) < count:
        raise RuntimeError(f"generated {len(rows)} non-M1 decoys, needed {count}")
    return tuple(rows)


def _has_immediate_mate(board: chess.Board) -> bool:
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        if after.is_checkmate():
            return True
    return False


def _hash_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    return output
