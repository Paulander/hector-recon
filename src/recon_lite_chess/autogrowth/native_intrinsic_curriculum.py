"""Native empty-learned-state KRK R0/R1 curriculum.

This runner joins the TG26p native graph substrate to the generic intrinsic
credit engine. Exact mate predicates are used only to construct trainer-side
curriculum pools. Training credit comes from an executed world transition or a
mature child's consolidated value; no correct-move set is passed to the learner.

Legacy runs retain the historical host-side action schedule.  Adaptive runs
instead ask the graph's anonymous local-choice mechanism to emit the action;
the harness executes and credits that exact emitted branch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import copy
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import math
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
    CompetenceSignal,
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
from .native_all_reply_envelope import (
    AvailabilityState,
    ReplyAuthority,
    evaluate_all_reply_envelope,
)
from .native_prospective_boundary_candidate_ecology import (
    BoundaryEcologyConfig,
    BoundaryObservation,
    ProspectiveBoundaryCandidateEcology,
    SketchLifecycle,
)
from .native_prospective_evidence_authority_v2 import (
    BoundaryPromotionRequest,
    PROVENANCE_COMMITMENT_V4,
    StructuralMode,
    _bounded_provenance_witnesses,
    _compact_set_commitment,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    ROOT_ID,
    _triplet_id,
    _triplet_keys,
)


R0_COMPETENCE_ID = "native_intrinsic_r0_mate_in_1"
R1_COMPETENCE_ID = "native_intrinsic_r1_mate_in_2"
V2_PROSPECTIVE_AVAILABILITY = "v2_prospective"
R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN = "sampled_round_robin"
R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE = "prospective_counterexample"
R1_REPLY_POLICIES = (
    R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN,
    R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
)
R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC = "lexicographic_round_robin"
R1_ACTION_ORDER_STABLE_HASH_PERMUTATION = "stable_hash_permutation"
R1_ACTION_SELECTION_SCHEDULED = "scheduled"
R1_ACTION_SELECTION_LOCAL_RECON = "local_recon_optimism"
R1_ACTION_SELECTION_MODES = (
    R1_ACTION_SELECTION_SCHEDULED,
    R1_ACTION_SELECTION_LOCAL_RECON,
)
R0_ACTION_SELECTION_SCHEDULED = R1_ACTION_SELECTION_SCHEDULED
R0_ACTION_SELECTION_LOCAL_RECON = R1_ACTION_SELECTION_LOCAL_RECON
R0_ACTION_SELECTION_MODES = R1_ACTION_SELECTION_MODES


def _strict_local_adaptive_mode(
    config: "NativeIntrinsicCurriculumConfig",
) -> bool:
    """Return whether competence authority is owned by local REAL evidence."""

    return bool(
        config.r0_boundary_ecology_enabled
        and not config.validation_controls_stage_transitions
        and config.r0_action_selection_mode
        == R0_ACTION_SELECTION_LOCAL_RECON
    )


# Short aliases keep the configuration readable for development callers while
# the canonical values remain explicit in snapshots and fingerprints.
R1_ACTION_ORDER_LEGACY = R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
R1_ACTION_ORDER_ADAPTIVE = R1_ACTION_ORDER_STABLE_HASH_PERMUTATION
R1_ACTION_ORDERS = (
    R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
    R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
)
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
    r0_action_selection_mode: str = R0_ACTION_SELECTION_SCHEDULED
    r1_reply_policy: str = R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN
    r1_action_selection_mode: str = R1_ACTION_SELECTION_SCHEDULED
    r1_action_order: str = R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
    r0_boundary_ecology_enabled: bool = False
    validation_controls_stage_transitions: bool = True
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

    def __post_init__(self) -> None:
        policy = str(self.r1_reply_policy).strip().lower()
        if policy not in R1_REPLY_POLICIES:
            raise ValueError(
                "r1_reply_policy must be sampled_round_robin or "
                "prospective_counterexample"
            )
        object.__setattr__(self, "r1_reply_policy", policy)
        selection_mode = str(self.r1_action_selection_mode).strip().lower()
        selection_aliases = {
            "local": R1_ACTION_SELECTION_LOCAL_RECON,
            "native": R1_ACTION_SELECTION_LOCAL_RECON,
            "native_local": R1_ACTION_SELECTION_LOCAL_RECON,
        }
        selection_mode = selection_aliases.get(selection_mode, selection_mode)
        if selection_mode not in R1_ACTION_SELECTION_MODES:
            raise ValueError(
                "r1_action_selection_mode must be scheduled or "
                "local_recon_optimism"
            )
        object.__setattr__(self, "r1_action_selection_mode", selection_mode)
        r0_selection_mode = str(self.r0_action_selection_mode).strip().lower()
        r0_selection_mode = selection_aliases.get(
            r0_selection_mode, r0_selection_mode
        )
        if r0_selection_mode not in R0_ACTION_SELECTION_MODES:
            raise ValueError(
                "r0_action_selection_mode must be scheduled or "
                "local_recon_optimism"
            )
        object.__setattr__(
            self, "r0_action_selection_mode", r0_selection_mode
        )
        action_order = str(self.r1_action_order).strip().lower()
        action_aliases = {
            "legacy": R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
            "lexicographic": R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
            "stable_hash": R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
            "hash_permutation": R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
        }
        action_order = action_aliases.get(action_order, action_order)
        if action_order not in R1_ACTION_ORDERS:
            raise ValueError(
                "r1_action_order must be lexicographic_round_robin or "
                "stable_hash_permutation"
            )
        object.__setattr__(self, "r1_action_order", action_order)


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
            "schema_version": "krk_native_intrinsic_r0_r1.v1",
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
        run_started=run_started,
    )
    # Legacy mode lets validation select an epoch, fit a gate, consolidate the
    # R0 graph, and open the next curriculum rung. Strict adaptive mode keeps
    # validation report-only and uses the already experienced training world
    # for its explicit curriculum boundary. In either mode, do not probe the
    # regression pool here: it is a final report and cannot become an indirect
    # stopping signal.
    r0_validation = _evaluate_r0(
        graph,
        pools.r0_validation,
        max_samples=cfg.max_samples,
        action_selection_mode=cfg.r0_action_selection_mode,
    )
    r0_regression: dict[str, Any] | None = None
    r0_validation_pass = bool(
        r0_validation["accuracy"] >= cfg.r0_mastery_threshold
        and r0_validation["illegal_move_count"] == 0
    )
    r0_training_policy_probe: dict[str, Any] | None = None
    r0_training_mastery_report: bool | None = None
    strict_local_adaptive = _strict_local_adaptive_mode(cfg)
    local_provider_audit: dict[str, Any] | None = None
    if cfg.validation_controls_stage_transitions:
        r0_pass = r0_validation_pass
        r0_stage_selection_source = "validation_outcome_mastery"
    elif strict_local_adaptive:
        # The fixed R0 interaction budget ends the phase.  Replaying the
        # learned policy on those same training positions is report-only;
        # exact graph decisions acquire authority below from their own REAL
        # returns, independently of this aggregate score.
        r0_training_policy_probe = _evaluate_r0(
            graph,
            pools.r0_train,
            max_samples=cfg.max_samples,
            action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        )
        r0_training_mastery_report = bool(
            r0_training_policy_probe["accuracy"]
            >= cfg.r0_mastery_threshold
            and r0_training_policy_probe["illegal_move_count"] == 0
        )
        local_provider_audit = (
            credit.consolidate_direct_outcome_providers(graph.triplet_ids)
        )
        r0_pass = bool(local_provider_audit["provider_count"] > 0)
        r0_stage_selection_source = (
            "local_direct_outcome_provider_readiness"
        )
    else:
        # Strict adaptive mode lets only training interaction decide whether
        # the learned R0 policy is ready to freeze.  This probe executes the
        # graph's own policy on the already experienced training environment;
        # it receives no correct move, mate-distance, or held-out signal.
        r0_training_policy_probe = _evaluate_r0(
            graph,
            pools.r0_train,
            max_samples=cfg.max_samples,
            action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        )
        r0_pass = bool(
            r0_training_policy_probe["accuracy"]
            >= cfg.r0_mastery_threshold
            and r0_training_policy_probe["illegal_move_count"] == 0
        )
        r0_stage_selection_source = "training_outcome_policy_mastery"

    r0_gate: OutcomeCalibratedPrototypeGate | None = None
    r0_gate_selection: dict[str, Any] | None = None
    r0_consolidation: dict[str, Any] = {
        "skipped": True,
        "reason": "r0_mastery_gate_failed",
    }
    if r0_pass and cfg.validation_controls_stage_transitions:
        r0_gate, r0_gate_selection = _fit_r0_gate(
            graph,
            train_positive=pools.r0_train,
            train_negative=pools.gate_train_decoys,
            validation_positive=pools.r0_validation,
            validation_negative=pools.gate_validation_decoys,
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
            "selection_source": r0_stage_selection_source,
        }
    elif r0_pass and not strict_local_adaptive:
        if r0_training_policy_probe is None:
            raise RuntimeError("training-selected R0 pass omitted its probe")
        disabled_training = _evaluate_r0(
            graph,
            pools.r0_train,
            masked_triplets=set(graph.triplet_ids),
            max_samples=0,
            action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        )
        credit.set_mature(R0_COMPETENCE_ID)
        intervention = credit.record_paired_intervention(
            R0_COMPETENCE_ID,
            enabled_return=float(r0_training_policy_probe["accuracy"]),
            disabled_return=float(disabled_training["accuracy"]),
        )
        deltas = credit.consolidate((R0_COMPETENCE_ID,))
        maturation = graph.mature_existing_graph()
        r0_consolidation = {
            "skipped": False,
            "paired_intervention": asdict(intervention),
            "value_consolidation_deltas": deltas,
            "competence": credit.snapshot()["states"][R0_COMPETENCE_ID],
            "gate": None,
            "gate_selection": None,
            "graph_maturation": maturation,
            "selection_source": r0_stage_selection_source,
            "training_policy_probe": r0_training_policy_probe,
            "disabled_training_policy_probe": disabled_training,
            "validation_influenced_maturity": False,
        }
    elif strict_local_adaptive:
        if local_provider_audit is None:
            raise RuntimeError("local R0 provider audit was not constructed")
        r0_consolidation = {
            "skipped": False,
            "selection_source": r0_stage_selection_source,
            "local_provider_audit": local_provider_audit,
            "global_r0_maturity_mutated": False,
            "global_paired_intervention_recorded": False,
            "graph_wide_maturation_performed": False,
            "aggregate_scores_report_only": True,
        }

    clone_parity = _clone_parity(graph, pools.r0_validation)
    if cfg.r0_replay_per_r1_epoch > 0:
        r0_replay_memory, r0_replay_memory_audit = _build_r0_replay_memory(
            graph,
            pools.r0_train,
        )
    else:
        # Strict adaptive runs forbid replay as a provider.  Do not even build
        # the old memoized move cache: an unreachable host-selected move table
        # is still needless plumbing and an avoidable future authority hazard.
        r0_replay_memory = ()
        r0_replay_memory_audit = {
            "enabled": False,
            "reason": "r0_replay_per_r1_epoch_is_zero",
            "cache_contains_memoized_move_provider": False,
            "experience_count": 0,
            "teacher_solution_labels_consumed": 0,
            "experiences": [],
        }
    r0_child_triplet_ids = frozenset(graph.triplet_ids)
    r0_parameter_freeze: dict[str, Any] = {
        "skipped": True,
        "reason": "disabled_or_r1_not_eligible",
    }
    if cfg.run_r1 and r0_pass and cfg.freeze_r0_parameters_for_r1:
        r0_parameter_freeze = graph.freeze_existing_parameters(
            reason=(
                "R0_validation_mastery_consolidation"
                if cfg.validation_controls_stage_transitions
                else (
                    "R0_local_direct_outcome_snapshot"
                    if strict_local_adaptive
                    else "R0_training_outcome_mastery_consolidation"
                )
            ),
            triplet_ids=(
                tuple(local_provider_audit["provider_ids"])
                if strict_local_adaptive
                and local_provider_audit is not None
                else None
            ),
        )
    r0_child_authority: Any | None = None
    r0_child_authority_audit: dict[str, Any] = {
        "enabled": False,
        "reason": "availability_mode_is_not_v2_prospective",
    }
    native_r0_admission: dict[str, Any] | None = None
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
        if cfg.r0_boundary_ecology_enabled:
            native_r0_admission = _native_v2_r0_admission_audit(
                authority,
                positive_fens=pools.r0_validation,
                negative_fens=pools.gate_validation_decoys,
                max_samples=cfg.max_samples,
            )
            r0_child_authority_audit["native_r0_admission"] = (
                native_r0_admission
            )
    # In V2 mode the authority already owns the immutable post-R0 organism.
    # Reuse that source graph for routing/report identity; frame-local queries
    # below run on its existing isolated dream session.  The non-V2 path has
    # no authority-owned source, so retain one report-only post-R0 copy.
    if r0_child_authority is not None:
        authority_r0 = getattr(getattr(r0_child_authority, "base", None), "r0", None)
        authority_graph = getattr(authority_r0, "graph", None)
        authority_triplets = getattr(authority_r0, "frozen_triplet_ids", None)
        if authority_graph is None or authority_triplets is None:
            raise TypeError(
                "V2 child authority does not expose its immutable R0 organism"
            )
        r0_core_graph = authority_graph
        r0_core_triplet_ids = frozenset(authority_triplets)
    else:
        r0_core_graph = copy.deepcopy(graph)
        r0_core_triplet_ids = frozenset(r0_core_graph.triplet_ids)
    # The host-side prototype gate remains available to legacy/control arms and
    # as a report-only diagnostic.  Adaptive V2 uses the prospectively
    # certified native authority as its sole runtime jurisdiction provider.
    # Keeping the objects distinct here prevents a successful kNN descriptor
    # from silently opening or preempting a native competence response.
    r0_core_gate = (
        None
        if r0_child_authority is not None and cfg.r0_boundary_ecology_enabled
        else r0_gate
    )
    r0_core_semantic_sha256 = _hash_json(
        r0_core_graph.canonical_semantic_manifest()
    )
    # The report source and the protected routing source are the same
    # post-R0 snapshot.  Keeping this explicit prevents future R1 changes
    # from silently changing the reported R0 competence.
    r0_report_graph = r0_core_graph
    progress: dict[str, Any] = {
        "schema_version": "krk_native_intrinsic_r0_r1_progress.v1",
        "ecology_uuid": ecology_uuid,
        "r0": {
            "pass": r0_pass,
            "pass_semantics": (
                "nonempty_local_direct_outcome_provider_set"
                if strict_local_adaptive
                else "aggregate_mastery_gate"
            ),
            "validation_accuracy": r0_validation["accuracy"],
            "training_mastery_report": r0_training_mastery_report,
            "local_provider_count": (
                0
                if local_provider_audit is None
                else int(local_provider_audit["provider_count"])
            ),
            "stopped_epoch": r0_training["stopped_epoch"],
            "stage_selection_source": r0_stage_selection_source,
            "availability_mode": cfg.r0_availability_mode,
            "regression_withheld_until_final": True,
        },
        "completed_r1_arms": {},
    }
    _write_json(cfg.progress_path, progress)
    arms: dict[str, Any] = {}
    selected_graph = graph
    selected_credit = credit
    availability_ready = bool(
        _native_v2_authority_ready_for_r1(
            availability_mode=cfg.r0_availability_mode,
            authority_present=r0_child_authority is not None,
            boundary_ecology_enabled=cfg.r0_boundary_ecology_enabled,
            admission_audit=native_r0_admission,
        )
        or (
            # The legacy prototype gate is a compatibility path for
            # non-V2 availability modes only.  In V2, native authority
            # integrity is the sole admission jurisdiction; allowing this
            # mature host gate to rescue a failed audit would fail open.
            cfg.r0_availability_mode != V2_PROSPECTIVE_AVAILABILITY
            and r0_gate is not None
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
            # Strict adaptive runs are organism training, not a factorial.
            # A cloned no-bootstrap arm is useful as a development control but
            # cannot steer the primary learner, so running it by default only
            # doubles cost and competes for the shared wall ceiling.
            legacy_names = ["full_intrinsic"]
            if not strict_local_adaptive:
                legacy_names.append("no_bootstrap")
            if cfg.run_redundant_child_ablation and not strict_local_adaptive:
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
            # A V2 arm clones the authority below; its own immutable R0 source
            # is therefore reused after that clone rather than copied again.
            arm_core_graph = (
                None
                if r0_child_authority is not None
                else copy.deepcopy(r0_core_graph)
            )
            arm_core_triplet_ids = (
                None
                if r0_child_authority is not None and r0_core_gate is None
                else r0_core_triplet_ids
            )
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
                r0_core_graph=arm_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=arm_core_triplet_ids,
                run_started=run_started,
                # Regression is a terminal report split.  Keep every arm's
                # training/validation work complete before any arm can read
                # either withheld regression pool.
                defer_regression_evaluation=True,
            )
            if arm_name == primary_arm_name:
                selected_graph = arm_graph
                selected_credit = arm_credit
            progress["completed_r1_arms"][arm_name] = _arm_progress_summary(
                arms[arm_name]
            )
            progress.pop("active_r1_arm", None)
            _write_json(cfg.progress_path, progress)

        # Legacy mode retains validation-selected consolidation.  Strict
        # adaptive mode leaves validation report-only: online local credit and
        # ecology mutation are already committed during REAL interaction.
        full_rate = arms[primary_arm_name]["validation"]["conversion_rate"]
        no_bootstrap_arm = arms.get("no_bootstrap")
        no_bootstrap_rate = (
            None
            if no_bootstrap_arm is None
            else no_bootstrap_arm["validation"]["conversion_rate"]
        )
        full_pass = (
            full_rate >= cfg.r1_mastery_threshold
            and arms[primary_arm_name]["r0_validation_retention"]["accuracy"]
            >= cfg.r0_mastery_threshold
        )
        if full_pass and cfg.validation_controls_stage_transitions:
            if no_bootstrap_rate is None:
                raise RuntimeError(
                    "validation-selected consolidation requires its "
                    "no-bootstrap control"
                )
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
        elif not cfg.validation_controls_stage_transitions:
            arms[primary_arm_name]["consolidation"] = {
                "skipped": True,
                "reason": "validation_is_report_only",
                "validation_influenced_learning": False,
            }

        # ``_run_r1_arm`` records its local state before the top-level
        # validation-selected consolidation.  Refresh the primary arm's
        # report snapshots so they describe the same post-mutation objects
        # that will be exposed as the final graph and credit state.
        if arms:
            arms[primary_arm_name]["graph"] = selected_graph.learned_state_audit()
            arms[primary_arm_name]["credit"] = selected_credit.snapshot()

        # Attach the held-out reports only after every validation-selected
        # graph/credit mutation above has finished.  This keeps regression
        # from becoming an arm-order-dependent stopping or selection signal,
        # and makes the primary arm's terminal report reflect the selected
        # post-consolidation graph and credit state.
        for arm in arms.values():
            _attach_terminal_r1_regression_report(arm, pools, cfg)

    r1_executed = bool(arms)
    primary_arm_name = (
        "exact_verify_learned_value"
        if cfg.r1_mechanistic_factorial
        else "full_intrinsic"
    )
    # This is intentionally a validation-only developmental decision.  The
    # held-out regression numbers are attached to the final report below but
    # cannot retroactively change maturity or stage advancement.
    r1_validation_pass = bool(
        r1_executed
        and arms[primary_arm_name]["validation"]["conversion_rate"]
        >= cfg.r1_mastery_threshold
        and arms[primary_arm_name]["r0_validation_retention"]["accuracy"]
        >= cfg.r0_mastery_threshold
    )
    development_directional_effect = (
        bool(
            arms[primary_arm_name]["validation"]["conversion_rate"]
            > arms["no_bootstrap"]["validation"]["conversion_rate"]
        )
        if r1_executed and "no_bootstrap" in arms
        else None
    )
    # A single development seed cannot establish a causal positive result.
    # Preserve the old field for consumers, but require a future preregistered
    # replicated analysis to set it true.
    causal_positive = False

    # Held-out regression is deliberately a terminal report operation.  R1
    # arms mutate only deep copies, so the original post-R0 graph remains the
    # exact R0 report source.  This is the only top-level R0 regression query.
    r0_regression = _evaluate_r0(
        r0_report_graph,
        pools.r0_regression,
        max_samples=cfg.max_samples,
        action_selection_mode=cfg.r0_action_selection_mode,
    )
    r0_regression_pass = bool(
        r0_regression["accuracy"] >= cfg.r0_mastery_threshold
        and r0_regression["illegal_move_count"] == 0
    )
    r0_gate_regression: dict[str, Any] | None = None
    if r0_gate is not None:
        r0_gate_regression = _evaluate_r0_gate_regression(
            r0_report_graph,
            r0_gate,
            positive_fens=pools.r0_regression,
            negative_fens=pools.gate_regression_decoys,
        )
        if r0_gate_selection is not None:
            r0_gate_selection = {
                **r0_gate_selection,
                "regression_metrics": r0_gate_regression,
                "regression_pass": bool(
                    r0_gate_regression["true_positive"]
                    == len(pools.r0_regression)
                    and r0_gate_regression["false_positive"] == 0
                ),
                "regression_evaluated_at_final": True,
            }
            if not r0_consolidation.get("skipped", True):
                r0_consolidation["gate_selection"] = r0_gate_selection

    r1_regression_pass_report_only = bool(
        r1_executed
        and arms[primary_arm_name].get("regression_pass_report_only", False)
    )
    r0_mastery_report_pass = bool(
        (
            r0_training_mastery_report
            if strict_local_adaptive
            and r0_training_mastery_report is not None
            else r0_pass
        )
        and r0_regression_pass
    )
    r0_final_report_pass = r0_mastery_report_pass
    # This is a terminal performance report, not an endogenous readiness
    # decision.  Neither validation nor regression is fed back into the graph,
    # credit engine, provider authority, or stage entry in strict local mode.
    r1_pass = bool(
        r1_validation_pass and r1_regression_pass_report_only
    )

    payload = {
        "scientific_contract": {
            "report_schema_version": "krk_native_intrinsic_r0_r1.v1",
            "progress_schema_version": "krk_native_intrinsic_r0_r1_progress.v1",
            "empty_means_empty_learned_state_not_absent_embodiment": True,
            "one_persistent_graph_across_rungs": True,
            "ecology_uuid": ecology_uuid,
            "native_formal_confirmation_used": True,
            "python_weighted_arbitration_used_for_r1_training": bool(
                cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_SCHEDULED
            ),
            "native_anonymous_choice_used_for_r1_training": bool(
                cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            # Learned values/exposures are native and exactly-one emission is
            # formal ReCoN. A generic adapter still enumerates affordances,
            # retrieves local sources, computes bounded curiosity, and packs
            # options; do not call the complete arbitration circuit in-graph.
            "r0_and_r1_runtime_action_sources_are_native_local": bool(
                cfg.r0_action_selection_mode
                == R0_ACTION_SELECTION_LOCAL_RECON
                and cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "formal_recon_exactly_one_emission_used_for_r0_and_r1": bool(
                cfg.r0_action_selection_mode
                == R0_ACTION_SELECTION_LOCAL_RECON
                and cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "generic_adapter_packages_local_competitors": bool(
                cfg.r0_action_selection_mode
                == R0_ACTION_SELECTION_LOCAL_RECON
                or cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "pure_in_graph_arbitration_claimed": False,
            "whole_curriculum_endogenous_claimed": False,
            "remaining_host_curriculum_controls": [
                "task_and_position_presentation",
                (
                    "fixed_r0_budget_and_content_blind_freeze_boundary"
                    if strict_local_adaptive
                    else "r0_training_outcome_stage_boundary"
                ),
                "worst_reply_environment_selection",
                "resource_ceilings_and_final_evaluation",
            ],
            "strict_adaptive_local_provider_grounding": (
                strict_local_adaptive
            ),
            "aggregate_r0_scores_are_report_only": strict_local_adaptive,
            "global_r0_competence_maturity_mutated": not (
                strict_local_adaptive
            ),
            "graph_wide_maturation_from_aggregate_score": not (
                strict_local_adaptive
            ),
            "local_provider_promotion_reads_only_direct_real_returns": (
                strict_local_adaptive
            ),
            "training_exploration": (
                "native_local_optimistic_competition_for_r0_and_r1"
                if (
                    cfg.r0_action_selection_mode
                    == R0_ACTION_SELECTION_LOCAL_RECON
                    and cfg.r1_action_selection_mode
                    == R1_ACTION_SELECTION_LOCAL_RECON
                )
                else (
                    "native_local_optimistic_competition_for_r1;"
                    "content_blind_round_robin_for_r0"
                    if cfg.r1_action_selection_mode
                    == R1_ACTION_SELECTION_LOCAL_RECON
                    else "content_blind_round_robin_over_formally_confirmed_legal_action_branches"
                )
            ),
            "r0_action_selection_mode": cfg.r0_action_selection_mode,
            "validation_controls_stage_transitions": (
                cfg.validation_controls_stage_transitions
            ),
            "learner_visible_stage_labels": False,
            "correct_move_labels_used_for_training_credit": False,
            "forced_move_labels_used_for_training_credit": False,
            "heldout_correct_move_labels_read": False,
            "r1_evaluation_uses_only_executed_all_reply_outcomes": True,
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
            "development_control_arms_executed": sorted(
                set(arms) - {primary_arm_name}
            ),
            "strict_training_runs_primary_arm_only": bool(
                strict_local_adaptive
            ),
            "exact_virtual_verification_is_oracle_control_not_autonomy_evidence": True,
            "prototype_gate_participates_in_current_runtime": bool(
                r0_child_authority is None
            ),
            "legacy_prototype_gate_retained_for_non_v2_modes": True,
            "composition_disabled_in_mechanistic_factorial": (
                cfg.r1_mechanistic_factorial
            ),
            "td_prediction_source": (
                "bounded_native_exploitation_value_used_by_local_policy_excluding_exploration"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else "exact_unrounded_confirmed_graph_action_score"
            ),
            "policy_ranking_value_transform": (
                "untried_generalized_prior:s/(1+abs(s));experienced_exact_q:identity"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else "identity"
            ),
            "td_prediction_uses_raw_graph_value": bool(
                cfg.r1_action_selection_mode
                != R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "policy_exploitation_score_and_td_prediction_identical": bool(
                cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "exploration_bonus_enters_td_prediction": False,
            "virtual_frames_create_grounding": False,
            "r0_replay_cache_used_as_provider": bool(
                cfg.r0_replay_per_r1_epoch > 0
            ),
            "adaptive_strict_profiles_disable_r0_replay_provider": bool(
                cfg.r0_action_selection_mode
                == R0_ACTION_SELECTION_LOCAL_RECON
                and cfg.r0_replay_per_r1_epoch == 0
            ),
            "r0_parameters_frozen_for_r1": cfg.freeze_r0_parameters_for_r1,
            "r0_child_queries_scoped_to_frozen_snapshot": True,
            # Legacy routing owns one report-only copy.  V2 routing instead
            # aliases the authority's serialized immutable R0 organism; it is
            # not copied again by this runner.
            "r0_core_execution_snapshot_is_deep_copied": bool(
                r0_child_authority is None
            ),
            "r0_core_execution_snapshot_authority_owned": bool(
                r0_child_authority is not None
            ),
            "r0_core_execution_snapshot_is_read_only": True,
            "r0_core_execution_source": (
                "authority.base.r0.graph_and_frozen_triplet_ids"
                if r0_child_authority is not None
                else "post_r0_report_copy"
            ),
            "r0_core_routing_scope": (
                "native_v2_certified_local_cells"
                if r0_child_authority is not None
                and cfg.r0_boundary_ecology_enabled
                else "all_policy_boards_local_gate_only"
            ),
            "r0_core_precedes_v2_when_available": bool(
                r0_core_gate is not None
            ),
            "adaptive_v2_host_prototype_gate_used_at_runtime": False,
            "r0_child_dispatch_cache_used_as_external_provider": False,
            "r0_child_dispatch_cache_is_memoized_graph_response": True,
            "r0_child_dispatch_hits_live_formally_confirmed": (
                cfg.r0_child_cache_validation_mode == "live_formal"
            ),
            "r0_child_dispatch_hits_frozen_policy_certified": (
                cfg.r0_child_cache_validation_mode == "frozen_policy_token"
            ),
            "runtime_child_priority_uses_stage_labels": False,
            "runtime_mature_child_priority_is_arm_specific": bool(
                cfg.r1_action_selection_mode
                != R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "runtime_child_priority_source": (
                "not_used_native_local_policy_plus_certified_successor"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else "explicit_mechanistic_arm"
            ),
            "adaptive_evaluation_host_priority_cascade_used": bool(
                cfg.r0_boundary_ecology_enabled
                and cfg.r1_action_selection_mode
                != R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "adaptive_evaluation_first_move_source": (
                "read_only_native_local_exploitation_policy"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else "legacy_host_routing"
            ),
            "adaptive_evaluation_successor_source": (
                "certified_native_v2_authority_fail_closed"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else "legacy_host_routing"
            ),
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
            "r1_virtual_reply_probe_schedule": (
                "exhaustive_all_legal_replies"
                if cfg.r1_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else "not_applicable"
            ),
            "r1_real_reply_challenge_schedule": (
                "worst_authority_state_then_confidence_then_selected_exposure"
                if cfg.r1_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else "per_position_action_round_robin"
            ),
            "r1_action_order": cfg.r1_action_order,
            "r1_action_selection_mode": cfg.r1_action_selection_mode,
            "r1_action_order_key": (
                "not_used_graph_local_anonymous_competition"
                if cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else (
                    "lexicographic_uci_ids"
                    if cfg.r1_action_order
                    == R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
                    else "generic_seed_plus_opaque_position_identity"
                )
            ),
            "hash_action_schedule_reachable_in_r1_training": bool(
                cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_SCHEDULED
                and cfg.r1_action_order
                == R1_ACTION_ORDER_STABLE_HASH_PERMUTATION
            ),
            "r1_reply_policy_requested": cfg.r1_reply_policy,
            "r1_reply_policy_requires_r0_child_authority": True,
            "r1_reply_policy_active": bool(
                cfg.r1_reply_policy == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                and r0_child_authority is not None
            ),
            "r1_all_reply_envelope_uses_only_virtual_pre_outcome_queries": True,
            "r1_all_reply_terminal_black_successors_are_refuted": True,
            "r1_all_reply_positive_handoff_requires_real_mate_and_clean_certification": True,
            "r1_td_successor_value_source": (
                "minimum_over_all_grounded_available_reply_values"
                if cfg.r1_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else "registered_mature_child_value"
            ),
            "r1_partial_or_unknown_envelope_value_reaches_td": False,
            "r0_and_r1_stopping_use_validation_only": bool(
                cfg.validation_controls_stage_transitions
            ),
            "r0_gate_fit_and_maturity_use_train_validation_only": bool(
                cfg.validation_controls_stage_transitions
            ),
            "r0_stage_entry_and_authority_use_validation_only": bool(
                cfg.validation_controls_stage_transitions
            ),
            "validation_outcome_mastery_is_report_only_for_stage_transitions": not bool(
                cfg.validation_controls_stage_transitions
            ),
            "validation_is_report_only_for_stage_transitions": bool(
                strict_local_adaptive
            ),
            "validation_runtime_integrity_safety_veto_may_block_stage_entry": bool(
                not cfg.validation_controls_stage_transitions
                and cfg.r0_boundary_ecology_enabled
            ),
            "training_outcome_policy_mastery_controls_r0_stage_entry": bool(
                not cfg.validation_controls_stage_transitions
                and not strict_local_adaptive
            ),
            "training_outcome_stage_boundary_is_harness_controlled": bool(
                not cfg.validation_controls_stage_transitions
                and not strict_local_adaptive
            ),
            "fixed_r0_budget_boundary_is_harness_controlled": (
                strict_local_adaptive
            ),
            "native_r0_coverage_specificity_is_report_only": bool(
                cfg.r0_boundary_ecology_enabled
            ),
            "native_r0_coverage_specificity_controls_r1_stage_entry": False,
            "native_r0_runtime_integrity_controls_r1_stage_entry": bool(
                cfg.r0_boundary_ecology_enabled
            ),
            "native_r0_runtime_integrity_reads_outcome_labels": False,
            "r1_checkpoint_retention_split": "r0_validation",
            "r1_checkpoint_retention_metric": (
                "r0_v2_shell_coverage_compatibility_alias"
                if (
                    r0_child_authority is not None
                    and cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
                    and cfg.r1_action_selection_mode
                    == R1_ACTION_SELECTION_LOCAL_RECON
                )
                else "r0_validation_retention"
            ),
            "r0_validation_retention_is_frozen_native_policy": not (
                r0_child_authority is not None
                and cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
                and cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "r0_frozen_native_policy_retention_reported": True,
            "r0_v2_shell_coverage_reported": bool(
                r0_child_authority is not None
                and cfg.r0_availability_mode == V2_PROSPECTIVE_AVAILABILITY
                and cfg.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            ),
            "regression_queries_in_progress": False,
            "r1_regression_withheld_until_final_evaluation": True,
            "r0_regression_withheld_until_final_evaluation": True,
            "r0_regression_report_source": "unmutated_post_r0_graph",
            "r0_gate_regression_report_only": True,
            "r1_alternate_routing_never_reads_regression": True,
            "adaptive_boundary_birth_requires_surprise_positive_outcome": bool(
                cfg.r0_boundary_ecology_enabled
            ),
            "adaptive_boundary_failures_are_contrast_only": bool(
                cfg.r0_boundary_ecology_enabled
            ),
            "adaptive_boundary_negative_promotions_forbidden": bool(
                cfg.r0_boundary_ecology_enabled
            ),
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
            "regression_withheld_until_final": True,
            "pass": r0_pass,
            "pass_semantics": (
                "nonempty_local_direct_outcome_provider_set"
                if strict_local_adaptive
                else "aggregate_mastery_gate"
            ),
            "validation_pass": r0_validation_pass,
            "stage_selection_source": r0_stage_selection_source,
            "training_policy_probe": r0_training_policy_probe,
            "training_mastery_report": r0_training_mastery_report,
            "local_provider_audit": local_provider_audit,
            "regression_pass_report_only": r0_regression_pass,
            "final_report_pass": r0_final_report_pass,
            "final_report_pass_semantics": (
                "aggregate_training_and_regression_performance_report_only"
                if strict_local_adaptive
                else "selected_stage_gate_and_regression_report"
            ),
            "endogenous_readiness_pass": r0_pass,
            "regression_source": "unmutated_post_r0_graph",
            "gate_regression_report": r0_gate_regression,
        },
        "clone_resume_probe": clone_parity,
        "r0_replay_memory": r0_replay_memory_audit,
        "r0_parameter_freeze": r0_parameter_freeze,
        "r0_core_routing": {
            "enabled": bool(r0_core_graph is not None and r0_core_gate is not None),
            "native_authority_only": bool(
                r0_child_authority is not None and r0_core_gate is None
            ),
            "operational": bool(
                _native_v2_runtime_integrity_ready(native_r0_admission)
            ),
            "scientific_admission_pass": bool(
                native_r0_admission is not None
                and native_r0_admission.get("pass", False)
            ),
            "graph": r0_core_graph.learned_state_audit(),
            "graph_semantic_state_sha256": r0_core_semantic_sha256,
            "triplet_ids": sorted(r0_core_triplet_ids),
            "gate": None if r0_core_gate is None else r0_core_gate.to_dict(),
            "precedes_v2_when_available": bool(r0_core_gate is not None),
            "routing_scope": (
                "native_local_direct_outcome_providers"
                if strict_local_adaptive
                and r0_child_authority is not None
                and r0_core_gate is None
                else "native_v2_certified_local_cells"
                if r0_child_authority is not None and r0_core_gate is None
                else "all_policy_boards_local_gate_only"
            ),
            "local_provider_precedes_outer_shell": bool(
                strict_local_adaptive and r0_child_authority is not None
            ),
            "stage_specific_preemption": False,
        },
        "r0_child_authority": r0_child_authority_audit,
        "r1_arms": arms,
        "final_graph": selected_graph.to_dict(),
        "final_credit": selected_credit.snapshot(),
        "decision": {
            "r0_pass": r0_pass,
            "r0_pass_semantics": (
                "nonempty_local_direct_outcome_provider_set"
                if strict_local_adaptive
                else "aggregate_mastery_gate"
            ),
            "r1_executed": r1_executed,
            "r1_pass": r1_pass,
            "r1_validation_pass": r1_validation_pass,
            "r1_final_report_pass": r1_pass,
            "r0_final_report_pass": r0_final_report_pass,
            "r0_final_report_pass_semantics": (
                "aggregate_performance_report_only"
                if strict_local_adaptive
                else "selected_gate_plus_regression"
            ),
            "r0_regression_pass_report_only": r0_regression_pass,
            "r1_regression_pass_report_only": r1_regression_pass_report_only,
            "primary_upper_bound_arm": primary_arm_name,
            "development_directional_effect_vs_no_bootstrap": development_directional_effect,
            "no_bootstrap_control_executed": "no_bootstrap" in arms,
            "r1_causal_positive_vs_no_bootstrap": causal_positive,
            "causal_claim_locked_pending_preregistered_seed_replication": True,
            "advance_to_r2": False,
            "interpretation": (
                "development_factorial_complete_no_r2_without_replication"
                if r1_executed
                else (
                    "native_r0_authority_integrity_failure_do_not_enter_r1"
                    if r0_pass
                    and cfg.r0_boundary_ecology_enabled
                    and native_r0_admission is not None
                    and not _native_v2_runtime_integrity_ready(
                        native_r0_admission
                    )
                    else "r0_failed_or_gate_unavailable_do_not_advance"
                )
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
    _regression_fens: Sequence[str],
    *,
    config: NativeIntrinsicCurriculumConfig,
    run_started: float | None = None,
) -> dict[str, Any]:
    episodes = mates = nonterminal = failures = 0
    started = perf_counter()
    ceiling_started = started if run_started is None else float(run_started)
    formal_confirmation_failures = 0
    local_action_count = 0
    scheduled_action_count = 0
    checkpoints: list[dict[str, Any]] = []
    stopped_epoch = config.r0_epochs
    for epoch in range(config.r0_epochs):
        for position_index, fen in enumerate(train_fens):
            board = chess.Board(fen)
            if (
                config.r0_action_selection_mode
                == R0_ACTION_SELECTION_LOCAL_RECON
            ):
                decision = graph.choose_local_training_action(
                    board,
                    stage_diagnostic="R0_mate_in_1",
                )
                move = decision.move
                triplet_id = decision.triplet_id
                confirmed = decision.confirmed
                graph_prediction = decision.prediction
                local_action_count += 1
            else:
                (
                    move,
                    triplet_id,
                    confirmed,
                    graph_prediction,
                ) = _scheduled_confirmed_action(
                    graph,
                    board,
                    schedule_index=epoch + position_index,
                    stage_diagnostic="R0_mate_in_1",
                )
                scheduled_action_count += 1
            formal_confirmation_failures += int(not confirmed)
            terminal_kind = _execute_white_and_observe(board, move)
            credit.register(triplet_id, hierarchy_depth=1)
            credit.begin_episode()
            responsibilities = (
                (Responsibility(triplet_id, parent_distance=0),)
                if _strict_local_adaptive_mode(config)
                else (
                    Responsibility(triplet_id, parent_distance=0),
                    Responsibility(R0_COMPETENCE_ID, parent_distance=1),
                )
            )
            event = credit.transition(
                triplet_id,
                responsibilities=responsibilities,
                terminal_kind=terminal_kind,
                prediction_override=graph_prediction,
            )
            graph.apply_intrinsic_td(
                board,
                move,
                td_error=event.td_error,
                stage_diagnostic="R0_mate_in_1",
                prediction_value=(
                    graph_prediction
                    if config.r0_action_selection_mode
                    == R0_ACTION_SELECTION_LOCAL_RECON
                    else None
                ),
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
        stop_after_validation = False
        if not should_validate:
            metrics = None
        else:
            metrics = _evaluate_r0(
                graph,
                validation_fens,
                max_samples=0,
                action_selection_mode=config.r0_action_selection_mode,
            )
            checkpoint = {
                "epoch": epoch + 1,
                "validation_accuracy": metrics["accuracy"],
                "validation_action_selection_mode": metrics[
                    "action_selection_mode"
                ],
                "triplet_count": len(graph.triplet_ids),
                "m3_update_count": graph.m3_update_count,
            }
            checkpoint["validation_mastery"] = bool(
                metrics["accuracy"] >= config.r0_mastery_threshold
            )
            if (
                checkpoint["validation_mastery"]
                and config.validation_controls_stage_transitions
            ):
                # Validation selects the stopping epoch.  The regression split is
                # evaluated once, after training, and cannot influence selection.
                stopped_epoch = epoch + 1
                stop_after_validation = True
            checkpoints.append(checkpoint)

        # Development ceilings are deliberately sampled only after all action
        # and TD work for this R0 epoch (and any requested validation) has
        # completed.  There is no R0 snapshot/resume protocol, so callers must
        # treat this exception as an interrupted, non-resumable attempt.
        ceiling_reason = None
        if (
            config.development_wall_ceiling_seconds is not None
            or config.development_peak_rss_ceiling_mib is not None
        ):
            ceiling_reason = _development_ceiling_reason(
                config,
                run_started=ceiling_started,
            )
        if ceiling_reason is not None:
            raise R0DevelopmentCeilingReached(
                epoch=epoch + 1,
                reason=ceiling_reason,
            )
        if stop_after_validation:
            break
    return {
        "episodes": episodes,
        "observed_mate_count": mates,
        "observed_nonterminal_count": nonterminal,
        "observed_failure_count": failures,
        "formal_confirmation_failure_count": formal_confirmation_failures,
        "r0_action_selection_mode": config.r0_action_selection_mode,
        "native_local_action_count": local_action_count,
        "scheduled_action_count": scheduled_action_count,
        "validation_controls_stage_transitions": (
            config.validation_controls_stage_transitions
        ),
        "stopped_epoch": stopped_epoch,
        "validation_checkpoints": checkpoints,
        "teacher_positive_move_sets_consumed": 0,
        "forced_first_move_labels_consumed": 0,
        "graph_after_training": graph.learned_state_audit(),
        "duration_seconds": round(perf_counter() - started, 6),
    }


class R0DevelopmentCeilingReached(RuntimeError):
    """Raised after a complete R0 epoch when a development ceiling binds.

    R0 has no checkpoint/resume protocol.  Keeping this distinct from the R1
    snapshot exception prevents a caller from accidentally presenting an R0
    boundary stop as resumable work.
    """

    def __init__(self, *, epoch: int, reason: str) -> None:
        super().__init__(
            f"R0 development ceiling reached after epoch {epoch}; "
            f"reason={reason}"
        )
        self.epoch = int(epoch)
        self.reason = str(reason)


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
        Path(__file__).with_name("native_all_reply_envelope.py").resolve(),
        Path(__file__).with_name("native_single_graph_curriculum.py").resolve(),
        Path(__file__).with_name("native_authority_handover.py").resolve(),
        Path(__file__).with_name("native_competence_envelope.py").resolve(),
        Path(__file__).with_name("native_trace_competence_authority.py").resolve(),
        Path(__file__).with_name(
            "native_prospective_evidence_authority_v2.py"
        ).resolve(),
        Path(__file__).with_name(
            "native_prospective_boundary_candidate_ecology.py"
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
    r0_gate: OutcomeCalibratedPrototypeGate | None,
    pools: _Pools,
    *,
    arm_name: str,
    arm_spec: R1MechanisticArm,
    r0_child_triplet_ids: frozenset[str],
    r0_child_authority_digest: str | None,
    config: NativeIntrinsicCurriculumConfig,
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
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
        "r0_gate": None if r0_gate is None else r0_gate.to_dict(),
        "r0_child_triplet_ids": sorted(r0_child_triplet_ids),
        "r0_child_authority_digest": r0_child_authority_digest,
        # A real V2 authority continuation digest already binds its immutable
        # R0 source.  Do not duplicate that graph in the arm fingerprint; the
        # optional fields remain for legacy direct callers without authority.
        "r0_core_graph_semantic_state_sha256": (
            None
            if r0_child_authority_digest is not None or r0_core_graph is None
            else _hash_json(r0_core_graph.canonical_semantic_manifest())
        ),
        "r0_core_triplet_ids": (
            []
            if r0_child_authority_digest is not None
            else sorted(
                r0_child_triplet_ids
                if r0_core_triplet_ids is None
                else r0_core_triplet_ids
            )
        ),
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


def _effective_r1_reply_policy(
    config: NativeIntrinsicCurriculumConfig,
    r0_child_authority: Any | None,
) -> str:
    """Resolve the requested policy without allowing it to bypass V2 authority."""

    requested = str(config.r1_reply_policy).strip().lower()
    if requested not in R1_REPLY_POLICIES:
        raise ValueError(f"unsupported R1 reply policy: {requested}")
    if (
        requested == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
        and r0_child_authority is not None
    ):
        return requested
    return R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN


def _r1_reply_counter_defaults() -> dict[str, int | float]:
    """Counters added by the opt-in all-reply policy.

    Keeping these defaults in one place lets old arm snapshots resume under the
    legacy policy while new snapshots carry the exact all-reply accounting.
    """

    return {
        "reply_envelope_count": 0,
        "reply_envelope_available_count": 0,
        "reply_envelope_unknown_count": 0,
        "reply_envelope_refuted_count": 0,
        "reply_envelope_positive_count": 0,
        "reply_virtual_query_count": 0,
        "reply_terminal_refuted_count": 0,
        "reply_counterexample_count": 0,
        "reply_counterexample_real_event_count": 0,
        "reply_counterexample_duplicate_virtual_count": 0,
        "reply_counterexample_mate_count": 0,
        "reply_counterexample_failure_count": 0,
        "reply_counterexample_surprise_success_count": 0,
        "reply_counterexample_false_authority_count": 0,
        "reply_counterexample_handoff_count": 0,
    }


def _record_r1_local_action_evidence(
    manifest: Mapping[str, Any],
    *,
    td_error: float,
    terminal_kind: str | None,
    successor_value: float,
    counters: dict[str, int | float],
    positive_credit_options: set[tuple[str, str]],
) -> bool:
    """Record report-only exact-option follow-through after successful TD.

    The learner never reads these counters or this identity set.  Unlike the
    presentation ring, they survive long runs and distinguish action aliases.
    The current positive event is added only after checking for a *prior*
    positive credit, so it cannot count as its own revisit.
    """

    exact_option = (str(manifest["pattern_id"]), str(manifest["move_uci"]))
    prior_exposure = int(manifest.get("action_option_exposure", 0))
    exact_q_selected = (
        manifest.get("prediction_source") == "learned_exact_action_value"
    )
    positive_credit_revisit = bool(
        exact_q_selected and exact_option in positive_credit_options
    )
    for key, increment in (
        ("local_action_first_contact_selections", prior_exposure == 0),
        ("local_action_post_contact_selections", prior_exposure > 0),
        ("local_action_exact_q_selections", exact_q_selected),
        ("local_action_positive_credit_revisits", positive_credit_revisit),
    ):
        counters[key] = counters.get(key, 0) + int(increment)
    if td_error > 0.0 and (terminal_kind == "mate" or successor_value > 0.0):
        positive_credit_options.add(exact_option)
    return positive_credit_revisit


def _r1_reply_policy_manifest(
    config: NativeIntrinsicCurriculumConfig,
    *,
    effective_policy: str,
    counters: Mapping[str, int | float],
    events: Sequence[Mapping[str, Any]],
    event_digest: str,
    exposure_counts: Mapping[tuple[str, str, str], int],
) -> dict[str, Any]:
    """Return bounded, exact policy telemetry suitable for snapshots/reports."""

    exposures = [
        {
            "fen": key[0],
            "white_move": key[1],
            "black_move": key[2],
            "reply_id": _r1_reply_id(*key),
            "exposure_count": int(value),
        }
        for key, value in sorted(exposure_counts.items())
    ]
    return {
        "schema_version": "native_intrinsic_r1_reply_policy.v1",
        "requested_policy": config.r1_reply_policy,
        "effective_policy": effective_policy,
        "active": effective_policy == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        "authority_required": True,
        "event_count": int(counters["reply_envelope_count"]),
        "event_digest": str(event_digest),
        "recent_event_limit": 16,
        "recent_event_count": len(events),
        "recent_events": list(events),
        "per_reply_exposure_count": len(exposures),
        "per_reply_exposures": exposures,
        "counter_summary": {
            key: int(value) if isinstance(value, int) else float(value)
            for key, value in sorted(counters.items())
            if key.startswith("reply_")
        },
    }


def _r1_reply_id(fen: str, white_move_uci: str, black_move_uci: str) -> str:
    """Return an opaque, stable identity for one exact reply exposure."""

    return "reply:" + _hash_json({
        "fen": str(fen),
        "white_move": str(white_move_uci),
        "black_move": str(black_move_uci),
    })


def _r1_reply_authority_from_classification(
    reply_id: str,
    classification: Mapping[str, Any] | Any,
    *,
    exposure_count: int,
    grounded: Any,
    provider_value: float | None = None,
    provider_confidence: float | None = None,
) -> ReplyAuthority:
    """Project a V2 classification into the generic envelope's read-set."""

    def field(name: str, default: Any) -> Any:
        if isinstance(classification, Mapping):
            return classification.get(name, default)
        return getattr(classification, name, default)

    raw_state = field("state", AvailabilityState.UNKNOWN.value)
    if isinstance(raw_state, AvailabilityState):
        state = raw_state
    else:
        try:
            state = AvailabilityState(str(raw_state).lower())
        except ValueError:
            state = AvailabilityState.UNKNOWN
    default_probability = {
        AvailabilityState.AVAILABLE: 1.0,
        AvailabilityState.REFUTED: 0.0,
        AvailabilityState.UNKNOWN: 0.5,
    }[state]
    try:
        probability = float(field("probability", default_probability))
    except (TypeError, ValueError):
        probability = default_probability
    default_uncertainty = (
        1.0 if state is AvailabilityState.UNKNOWN else 1.0 - probability
    )
    try:
        uncertainty = float(field("uncertainty", default_uncertainty))
    except (TypeError, ValueError):
        uncertainty = default_uncertainty
    if not math.isfinite(probability):
        probability = default_probability
    if not math.isfinite(uncertainty):
        uncertainty = default_uncertainty
    probability = max(0.0, min(1.0, probability))
    uncertainty = max(0.0, min(1.0, uncertainty))
    # ``confidence`` keeps the classification probability; ``value`` is the
    # usable part after uncertainty.  UNKNOWN therefore cannot open the
    # envelope, and a low-confidence AVAILABLE row cannot self-bootstrap.
    # Grounding is a provenance capability, not a truthy configuration bit.
    # Accept only the exact boolean type so missing values, strings, and
    # integer sentinels cannot silently open a child envelope.
    grounded_value = grounded if type(grounded) is bool else False
    value = 1.0 - uncertainty
    if provider_value is not None:
        try:
            local_value = float(provider_value)
        except (TypeError, ValueError):
            grounded_value = False
        else:
            if not math.isfinite(local_value) or not 0.0 < local_value <= 1.0:
                grounded_value = False
            else:
                value = min(value, local_value)
    if provider_confidence is not None:
        try:
            local_confidence = float(provider_confidence)
        except (TypeError, ValueError):
            grounded_value = False
        else:
            if (
                not math.isfinite(local_confidence)
                or not 0.0 < local_confidence <= 1.0
            ):
                grounded_value = False
            else:
                probability = min(probability, local_confidence)
    return ReplyAuthority(
        reply_id=str(reply_id),
        state=state,
        confidence=probability,
        value=value,
        exposure_count=int(exposure_count),
        grounded=grounded_value,
    )


def _r1_terminal_reply_authority(
    reply_id: str,
    *,
    exposure_count: int,
) -> ReplyAuthority:
    """Represent a terminal black-reply successor as a formal REFUTED row."""

    return ReplyAuthority(
        reply_id=str(reply_id),
        state=AvailabilityState.REFUTED,
        confidence=0.0,
        value=0.0,
        exposure_count=int(exposure_count),
        grounded=True,
    )


def _r1_reply_authority_from_provider(
    reply_id: str,
    provider: Mapping[str, Any],
    *,
    exposure_count: int,
) -> ReplyAuthority:
    """Project one graph-selected, locally grounded native provider."""

    try:
        cell_id = provider["cell_id"]
        authority_cell_id = provider["authority_cell_id"]
        provider_kind = provider["provider_kind"]
        schema_version = provider["schema_version"]
        hypothesis_digest = provider["hypothesis_digest"]
        receipt_digest = provider["certification_receipt_digest"]
        raw_value = provider["expected_value"]
        raw_confidence = provider["confidence"]
        raw_uncertainty = provider["uncertainty"]
        direct_positive = provider["direct_positive_evidence"]
        direct_contrast = provider["direct_contrast_evidence"]
        receipt_count = provider["certification_receipt_count"]
        grounding_level = provider["grounding_level"]
        raw_ancestors = provider["grounding_ancestors"]
        if any(
            isinstance(item, bool)
            for item in (raw_value, raw_confidence, raw_uncertainty)
        ) or any(
            isinstance(item, bool) or not isinstance(item, int)
            for item in (
                direct_positive,
                direct_contrast,
                receipt_count,
                grounding_level,
            )
        ):
            raise TypeError("malformed provider scalar")
        if not isinstance(raw_ancestors, (tuple, list)):
            raise TypeError("malformed provider ancestry")
        grounding_ancestors = tuple(raw_ancestors)
        value = float(raw_value)
        confidence = float(raw_confidence)
        uncertainty = float(raw_uncertainty)
    except (KeyError, TypeError, ValueError, OverflowError):
        value = confidence = 0.0
        uncertainty = 1.0
        direct_positive = 0
        direct_contrast = 1
        receipt_count = -1
        grounding_level = -1
        grounding_ancestors = ()
        cell_id = authority_cell_id = provider_kind = schema_version = None
        hypothesis_digest = receipt_digest = None
    digest_valid = lambda value: bool(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
    valid = bool(
        isinstance(cell_id, str)
        and cell_id
        and isinstance(authority_cell_id, str)
        and authority_cell_id
        and digest_valid(hypothesis_digest)
        and digest_valid(receipt_digest)
        and math.isfinite(value)
        and 0.0 < value <= 1.0
        and math.isfinite(confidence)
        and 0.0 < confidence <= 1.0
        and math.isfinite(uncertainty)
        and 0.0 <= uncertainty < 1.0
        and math.isclose(
            confidence + uncertainty,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        and direct_positive > 0
        and direct_contrast == 0
        and receipt_count == direct_positive
        and grounding_level >= 0
        and all(
            isinstance(item, str) and item
            for item in grounding_ancestors
        )
        and tuple(sorted(set(grounding_ancestors)))
        == grounding_ancestors
    )
    if provider_kind == "prospective_authority_cell":
        raw_support = provider.get("support")
        raw_successes = provider.get("successes")
        raw_contradictions = provider.get("contradictions")
        valid = bool(
            valid
            and schema_version == "native_prospective_provider.v1"
            and authority_cell_id == cell_id
            and provider.get("prospectively_certified") is True
            and provider.get("postbirth_real_certification") is True
            and provider.get("discovery_evidence_used") is False
            and provider.get("evidence_scope")
            == "post_birth_real_certification_ledger"
            and provider.get("grounding_source")
            == "prospective_postbirth_real_certification"
            and math.isclose(
                value,
                confidence,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            and not any(
                isinstance(item, bool) or not isinstance(item, int)
                for item in (
                    raw_support,
                    raw_successes,
                    raw_contradictions,
                )
            )
            and raw_support == receipt_count
            and raw_successes == direct_positive
            and raw_contradictions == direct_contrast
        )
    elif provider_kind == "native_direct_outcome_cell":
        valid = bool(
            valid
            and schema_version == "native_direct_provider.v1"
            and cell_id == f"native-r0-provider:{authority_cell_id}"
            and provider.get("direct_outcome_authorized") is True
            and provider.get("prospectively_certified") is False
            and provider.get("postbirth_real_certification") is False
            and provider.get("discovery_evidence_used") is False
            and provider.get("evidence_scope")
            == "exact_selected_real_return_ledger"
            and provider.get("grounding_source")
            == "exact_selected_real_returns"
        )
    else:
        valid = False
    return ReplyAuthority(
        reply_id=str(reply_id),
        state=(
            AvailabilityState.AVAILABLE
            if valid
            else AvailabilityState.UNKNOWN
        ),
        confidence=confidence if valid else 0.0,
        value=value if valid else 0.0,
        exposure_count=int(exposure_count),
        grounded=valid,
    )


def _r1_reply_authority_from_local_provider(
    reply_id: str,
    provider: Mapping[str, Any],
    *,
    exposure_count: int,
) -> ReplyAuthority:
    """Backward-compatible name for the general native provider adapter."""

    return _r1_reply_authority_from_provider(
        reply_id,
        provider,
        exposure_count=exposure_count,
    )


def _r1_terminal_reply_terminal_kind(terminal_kind: str | None) -> str:
    """Map a terminal black reply to the R1 credit channel."""

    return {
        "stalemate": "horizon",
        "rook_loss": "rook_loss",
        "mate": "failure",
    }.get(str(terminal_kind), "failure")


def _protected_core_r0_available(
    graph: NativeReConKRKGraph,
    gate: OutcomeCalibratedPrototypeGate,
    board: chess.Board,
    *,
    allowed_triplets: frozenset[str],
    authority: Any | None = None,
    frame_session: Any | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Return a grounded local-core capability without touching V2 history.

    The gate is fitted from the post-R0 local policy response.  A positive
    gate result is usable only when the frozen graph emitted a legal,
    in-snapshot candidate.  This keeps a descendant/V2 classification from
    opening the all-reply envelope by itself, while retaining the raw V2
    response for audit and real-event accounting.
    """

    if not allowed_triplets.issubset(graph.triplet_ids):
        raise ValueError("protected R0 core triplet ids are not in its graph")
    # Reuse the authority's existing frame runtime whenever one is active.
    # Otherwise, if the supplied source is that authority's persistent R0
    # graph, create one short-lived dream session so this outcome-free query
    # cannot mutate the serialized source.  Direct non-V2 tests may still pass
    # an explicit isolated graph and use it unchanged.
    runtime_graph = None
    if frame_session is not None:
        runtime_graph = getattr(
            getattr(frame_session, "r0_session", None),
            "virtual_graph",
            None,
        )
    temporary_session = None
    authority_r0 = getattr(getattr(authority, "base", None), "r0", None)
    authority_graph = getattr(authority_r0, "graph", None)
    if runtime_graph is None and authority_graph is graph:
        dream_session = getattr(authority_r0, "dream_session", None)
        if callable(dream_session):
            temporary_session = dream_session()
            runtime_graph = getattr(temporary_session, "virtual_graph", None)
    if runtime_graph is None:
        runtime_graph = graph
    if not allowed_triplets.issubset(runtime_graph.triplet_ids):
        if temporary_session is not None:
            temporary_session.close()
        raise ValueError("protected R0 runtime is missing frozen triplets")
    try:
        available, response = _r0_available(
            runtime_graph,
            gate,
            board,
            mode="prototype_gate",
            allowed_triplets=allowed_triplets,
        )
    finally:
        if temporary_session is not None:
            temporary_session.close()
    selected_uci = response.get("selected_move")
    selected_triplet = response.get("selected_triplet")
    legal = False
    if selected_uci is not None:
        try:
            legal = chess.Move.from_uci(str(selected_uci)) in board.legal_moves
        except ValueError:
            legal = False
    # ``mature`` and the legal in-snapshot policy response are deliberately
    # checked separately from ``confirms``.  A malformed/fake truthy field is
    # never promoted to grounding by this adapter.
    grounded = bool(
        type(getattr(gate, "mature", None)) is bool
        and gate.mature
        and available
        and legal
        and selected_triplet is not None
        and str(selected_triplet) in allowed_triplets
    )
    probability = 0.0
    probability_fn = getattr(gate, "probability", None)
    if callable(probability_fn):
        try:
            probability = float(probability_fn(response["features"]))
        except (TypeError, ValueError):
            probability = 0.0
    elif grounded:
        # Small deterministic test doubles may expose only ``confirms``.  A
        # positive value here still requires the explicit boolean grounding
        # checks above; production gates always provide ``probability``.
        probability = 1.0
    if not math.isfinite(probability):
        probability = 0.0
    probability = max(0.0, min(1.0, probability))
    response = {
        **response,
        "available": grounded,
        "grounded": grounded,
        "grounding_source": (
            "frozen_r0_local_competence_gate" if grounded else None
        ),
        "core_gate_probability": probability,
        "core_policy_response_valid": legal and selected_triplet is not None,
        "availability_source": "frozen_r0_local_competence_gate",
    }
    return grounded, response


def _r1_reply_authority_from_core_response(
    reply_id: str,
    response: Mapping[str, Any],
    *,
    exposure_count: int,
) -> ReplyAuthority:
    """Project only grounded protected-core evidence into the envelope."""

    grounded = type(response.get("grounded")) is bool and response["grounded"]
    probability = float(response.get("core_gate_probability", 0.0))
    if not math.isfinite(probability):
        probability = 0.0
    probability = max(0.0, min(1.0, probability))
    raw_value = response.get("core_authority_value")
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = 0.0
    value_valid = math.isfinite(value) and 0.0 < value <= 1.0
    if not grounded or not value_valid:
        return ReplyAuthority(
            reply_id=str(reply_id),
            state=AvailabilityState.UNKNOWN,
            confidence=0.0,
            value=0.0,
            exposure_count=int(exposure_count),
            grounded=False,
        )
    return ReplyAuthority(
        reply_id=str(reply_id),
        state=AvailabilityState.AVAILABLE,
        confidence=probability,
        value=value,
        exposure_count=int(exposure_count),
        grounded=True,
    )


def _v2_grounding_audit(
    authority: Any,
) -> tuple[bool, dict[str, Any]]:
    """Read the V2 provider's explicit grounding capability, fail closed.

    The local frozen-core gate is an outcome-calibrated routing predicate, but
    it is not itself the V2 authority's provenance capability.  Training may
    project either signal into the all-reply envelope only after the native
    child provider explicitly says it is grounded.  ``mature`` and
    ``can_emit`` are required when the provider exposes them (the production
    ``FrozenCompetenceProvenance`` always does); accepting a small test double
    that omits those fields does not weaken the exact-boolean grounded check.
    """

    r0 = getattr(getattr(authority, "base", None), "r0", None)
    provenance = getattr(r0, "provenance", None)
    direct_provider_ids = tuple(
        sorted(getattr(r0, "direct_provider_ids", ()))
    )
    if direct_provider_ids:
        return True, {
            "grounded": True,
            "mature": True,
            "can_emit": True,
            "grounding_source": "exact_selected_real_returns",
            "consolidated_value": None,
            "explicit_grounding_valid": True,
            "local_direct_outcome_mode": True,
            "direct_provider_count": len(direct_provider_ids),
            "direct_provider_ids": list(direct_provider_ids),
        }
    raw_grounded = getattr(provenance, "grounded", None)
    raw_mature = getattr(provenance, "mature", None)
    raw_can_emit = getattr(provenance, "can_emit", None)
    grounded = type(raw_grounded) is bool and raw_grounded
    if raw_mature is not None:
        grounded = grounded and type(raw_mature) is bool and raw_mature
    if raw_can_emit is not None:
        grounded = grounded and type(raw_can_emit) is bool and raw_can_emit
    audit = {
        "grounded": raw_grounded,
        "mature": raw_mature,
        "can_emit": raw_can_emit,
        "grounding_source": getattr(provenance, "grounding_source", None),
        "consolidated_value": getattr(provenance, "consolidated_value", None),
        "explicit_grounding_valid": bool(grounded),
        "local_direct_outcome_mode": False,
        "direct_provider_count": 0,
        "direct_provider_ids": [],
    }
    return bool(grounded), audit


def _core_response_for_v2_training(
    authority: Any,
    response: Mapping[str, Any],
) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    """Overlay local core routing with explicit V2 provenance.

    The local gate may recognize a frozen R0 region, but an all-reply
    successor handoff still needs a grounded native provider.  Keep the local
    result and raw provenance visible while exposing only the conjunction as
    the effective core capability.
    """

    v2_grounded, grounding = _v2_grounding_audit(authority)
    local_available = bool(response.get("available", False))
    raw_value = grounding.get("consolidated_value")
    try:
        authority_value = float(raw_value)
    except (TypeError, ValueError):
        authority_value = 0.0
    value_valid = math.isfinite(authority_value) and 0.0 < authority_value <= 1.0
    effective = bool(local_available and v2_grounded and value_valid)
    effective_response = {
        **dict(response),
        "local_core_available": local_available,
        "local_core_grounded": bool(response.get("grounded", False)),
        "available": effective,
        "grounded": effective,
        "grounding_source": (
            "frozen_r0_local_competence_gate"
            if effective else None
        ),
        "core_authority_value": authority_value if value_valid else raw_value,
        "core_authority_value_valid": value_valid,
        "v2_provenance_grounding": grounding,
        "core_authority_grounding_required": True,
    }
    return effective, effective_response, grounding


def _grounded_all_reply_successor_signal(
    envelope: Any,
    *,
    bootstrap_enabled: bool,
    actual_mate: bool,
    clean_preoutcome_evidence: bool,
    credit: IntrinsicCreditEngine | None = None,
    provider_ids: Sequence[str] = (),
    provider_records: Mapping[str, Mapping[str, Any]] | None = None,
    external_provider_resolver: Any | None = None,
    strict_adaptive: bool = False,
) -> CompetenceSignal | None:
    """Compose the exact worst-reply value without inventing a provider.

    The all-reply graph has already reduced the reply set with an AND gate and
    a minimum value.  Only a clean, outcome-confirmed handoff may expose that
    composition to TD credit.  Exact R0 decisions resolve through the shared
    credit graph; generalized shell cells resolve through their own authority
    ledger.  The envelope itself is never registered as a synthetic cell.
    """

    if not (
        bootstrap_enabled
        and actual_mate
        and clean_preoutcome_evidence
        and envelope.state is AvailabilityState.AVAILABLE
        and bool(envelope.positive_gate)
        and envelope.replies
    ):
        return None
    value = float(envelope.value)
    confidence = min(float(row.confidence) for row in envelope.replies)
    if (
        not math.isfinite(value)
        or value <= 0.0
        or not math.isfinite(confidence)
        or confidence <= 0.0
    ):
        return None
    normalized_provider_ids = tuple(sorted(set(map(str, provider_ids))))
    captured_records = (
        {}
        if provider_records is None
        else {
            str(key): dict(record)
            for key, record in provider_records.items()
            if isinstance(record, Mapping)
        }
    )
    if set(captured_records).difference(normalized_provider_ids):
        return None
    grounding_level = 1
    grounding_ancestors: tuple[str, ...]
    if normalized_provider_ids:
        if credit is None:
            raise ValueError("local all-reply providers require credit state")
        provider_levels: list[int] = []
        ancestors = set(normalized_provider_ids)
        for provider_id in normalized_provider_ids:
            captured = captured_records.get(provider_id)
            if captured is None:
                # Historical/non-strict callers may still compose providers
                # registered in this exact credit engine.  Strict adaptive
                # training never substitutes a plastic same-ID state for the
                # frozen authority that emitted a reply.
                if strict_adaptive:
                    return None
                state = credit.states.get(provider_id)
                local = credit.direct_outcome_provider_response(provider_id)
                if state is None or local is None:
                    return None
                provider_levels.append(int(local["grounding_level"]))
                ancestors.update(local["grounding_ancestors"])
                if (
                    value > float(local["expected_value"]) + 1e-12
                    or confidence > float(local["confidence"]) + 1e-12
                ):
                    return None
                continue
            if not callable(external_provider_resolver):
                return None
            current = external_provider_resolver(provider_id)
            if not isinstance(current, Mapping):
                return None
            captured_row = _r1_reply_authority_from_provider(
                "captured-provider",
                captured,
                exposure_count=0,
            )
            current_row = _r1_reply_authority_from_provider(
                "current-provider",
                current,
                exposure_count=0,
            )
            if not captured_row.grounded or not current_row.grounded:
                return None
            try:
                captured_count = captured["certification_receipt_count"]
                current_count = current["certification_receipt_count"]
                captured_level = captured["grounding_level"]
                captured_ancestors = tuple(
                    captured["grounding_ancestors"]
                )
                current_level = current["grounding_level"]
                current_ancestors = tuple(current["grounding_ancestors"])
            except (KeyError, TypeError, ValueError, OverflowError):
                return None
            if (
                current.get("cell_id") != provider_id
                or captured.get("cell_id") != provider_id
                or current.get("authority_cell_id")
                != captured.get("authority_cell_id")
                or current.get("provider_kind")
                != captured.get("provider_kind")
                or current.get("hypothesis_digest")
                != captured.get("hypothesis_digest")
                or isinstance(captured_count, bool)
                or not isinstance(captured_count, int)
                or isinstance(current_count, bool)
                or not isinstance(current_count, int)
                or current_count not in {
                    captured_count,
                    captured_count + 1,
                }
                or (
                    captured.get("provider_kind")
                    == "native_direct_outcome_cell"
                    and current_count != captured_count
                )
                or isinstance(captured_level, bool)
                or not isinstance(captured_level, int)
                or captured_level < 0
                or current_level != captured_level
                or tuple(sorted(set(captured_ancestors)))
                != captured_ancestors
                or current_ancestors != captured_ancestors
                or (
                    current_count == captured_count
                    and current.get("certification_receipt_digest")
                    != captured.get("certification_receipt_digest")
                )
                or (
                    current_count == captured_count + 1
                    and current.get("certification_receipt_digest")
                    == captured.get("certification_receipt_digest")
                )
                or value > float(captured["expected_value"]) + 1e-12
                or confidence > float(captured["confidence"]) + 1e-12
            ):
                return None
            provider_levels.append(captured_level)
            ancestors.update(captured_ancestors)
        grounding_level = 1 + max(provider_levels)
        grounding_ancestors = tuple(sorted(ancestors))
    else:
        if strict_adaptive:
            return None
        normalized_provider_ids = (R0_COMPETENCE_ID,)
        grounding_ancestors = (R0_COMPETENCE_ID,)
    return CompetenceSignal(
        value=value,
        confidence=min(1.0, confidence),
        provider_ids=normalized_provider_ids,
        grounding_level=grounding_level,
        grounding_ancestors=grounding_ancestors,
    )


def _prospective_counterexample_reply_probe(
    authority: Any,
    after_first: chess.Board,
    *,
    fen: str,
    white_move_uci: str,
    exposure_counts: dict[tuple[str, str, str], int],
    frame_prefix: str,
    frame_session: Any | None,
    generic_seed: int,
    strict_adaptive: bool = False,
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Probe every black reply virtually and settle one formal challenge.

    The returned successor boards are transient host values.  The authority is
    touched only through ``_v2_r0_available`` (VIRTUAL) in this helper; the
    selected successor is committed by the caller after the envelope settles.
    """

    replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
    if not replies:
        raise ValueError("all-reply probe requires at least one black reply")
    core_supplied = bool(
        r0_core_graph is not None
        or r0_core_gate is not None
        or r0_core_triplet_ids is not None
    )
    core_enabled = bool(
        r0_core_graph is not None
        and r0_core_gate is not None
        and r0_core_triplet_ids is not None
    )
    if core_supplied and not core_enabled:
        raise ValueError(
            "all-reply core routing requires graph, gate, and triplet ids"
        )
    if core_enabled and not r0_core_triplet_ids.issubset(r0_core_graph.triplet_ids):
        raise ValueError("protected R0 core triplet ids are not in its graph")
    authority_rows: list[ReplyAuthority] = []
    contexts: list[dict[str, Any]] = []
    virtual_query_count = terminal_refuted_count = 0
    for reply_index, reply in enumerate(replies):
        black_move_uci = reply.uci()
        key = (str(fen), str(white_move_uci), black_move_uci)
        exposure_count = int(exposure_counts.get(key, 0))
        reply_id = _r1_reply_id(*key)
        successor = after_first.copy(stack=False)
        successor.push(reply)
        terminal_kind = _terminal_kind(successor)
        if terminal_kind is not None:
            classification = {
                "state": AvailabilityState.REFUTED.value,
                "probability": 0.0,
                "uncertainty": 1.0,
                "available_cell_ids": [],
                "refuted_cell_ids": [],
                "formal_available": False,
                "formal_refuted": True,
                "policy_response": False,
            }
            authority_row = _r1_terminal_reply_authority(
                reply_id,
                exposure_count=exposure_count,
            )
            terminal_refuted_count += 1
            v2_available = False
            v2_response: dict[str, Any] | None = None
            v2_grounding: dict[str, Any] | None = None
            core_response: dict[str, Any] | None = None
            effective_core_response: dict[str, Any] | None = None
            local_provider: Mapping[str, Any] | None = None
            provider: Mapping[str, Any] | None = None
            provider_kind: str | None = None
            core_available = False
            effective_core_available = False
        else:
            v2_available, v2_response = _v2_r0_available(
                authority,
                successor,
                frame_id=f"{frame_prefix}:reply:{reply_index}:{black_move_uci}",
                frame_session=frame_session,
            )
            classification = dict(v2_response.get("classification", {}))
            v2_grounded, v2_grounding = _v2_grounding_audit(authority)
            local_provider = v2_response.get("local_provider")
            provider = v2_response.get("provider")
            if not isinstance(provider, Mapping):
                provider = None
            provider_kind = (
                str(v2_response.get("provider_kind"))
                if provider is not None
                else None
            )
            if isinstance(provider, Mapping):
                authority_row = _r1_reply_authority_from_provider(
                    reply_id,
                    provider,
                    exposure_count=exposure_count,
                )
                is_direct_provider = bool(
                    provider_kind == "native_direct_outcome_cell"
                )
                core_available = bool(
                    authority_row.grounded and is_direct_provider
                )
                effective_core_available = core_available
                core_response = (
                    dict(v2_response) if is_direct_provider else None
                )
                effective_core_response = {
                    **dict(v2_response),
                    "available": authority_row.grounded,
                    "grounded": authority_row.grounded,
                    "availability_source": provider_kind,
                }
            elif core_enabled and not strict_adaptive:
                core_available, core_response = _protected_core_r0_available(
                    r0_core_graph,
                    r0_core_gate,
                    successor,
                    allowed_triplets=r0_core_triplet_ids,
                    authority=authority,
                    frame_session=frame_session,
                )
                effective_core_available, effective_core_response, _ = (
                    _core_response_for_v2_training(authority, core_response)
                )
                if effective_core_available:
                    # The local protected core wins.  V2 cannot veto a
                    # grounded native core response, but its raw classification
                    # remains in the context for audit.
                    authority_row = _r1_reply_authority_from_core_response(
                        reply_id,
                        effective_core_response,
                        exposure_count=exposure_count,
                    )
                else:
                    # Core abstention is genuine delegation, not a global
                    # negative veto: a separately grounded/certified V2
                    # descendant may still serve as the effective row.
                    authority_row = _r1_reply_authority_from_classification(
                        reply_id,
                        classification,
                        exposure_count=exposure_count,
                        grounded=(
                            False
                            if strict_adaptive
                            else v2_response.get("grounded")
                        ),
                    )
            else:
                core_available = False
                core_response = None
                effective_core_available = False
                effective_core_response = None
                authority_row = _r1_reply_authority_from_classification(
                    reply_id,
                    classification,
                    exposure_count=exposure_count,
                    grounded=(
                        False
                        if strict_adaptive
                        else v2_response.get("grounded")
                    ),
                )
            virtual_query_count += 1
        authority_rows.append(authority_row)
        contexts.append({
            "reply_id": reply_id,
            "black_move": black_move_uci,
            "successor": successor,
            "terminal_kind": terminal_kind,
            "classification": classification,
            "v2_available": bool(v2_available),
            "v2_response": v2_response,
            "v2_grounding": v2_grounding,
            "core_available": bool(core_available),
            "core_response": core_response,
            "effective_core_available": bool(effective_core_available),
            "effective_core_response": effective_core_response,
            "provider_id": (
                None
                if provider is None
                else provider.get("cell_id")
            ),
            "provider_kind": provider_kind,
            "provider_record": (
                None if provider is None else dict(provider)
            ),
            "effective_available": bool(
                authority_row.state is AvailabilityState.AVAILABLE
                and authority_row.grounded
            ),
            # A protected-core row makes descendant false IDs audit-only;
            # grounded V2 fallback retains normal descendant evidence rules.
            "effective_source": (
                "terminal_refuted"
                if terminal_kind is not None
                else (
                    str(provider_kind)
                    if provider is not None
                    else (
                        "frozen_r0_local_competence_gate"
                        if effective_core_available
                        else (
                            "v2_grounded_descendant"
                            if authority_row.grounded
                            else "unknown"
                        )
                    )
                )
            ),
            "authority_row": authority_row,
            "exposure_count": exposure_count,
            "exposure_key": key,
        })
    envelope_id = f"{frame_prefix}:all-reply"
    envelope = evaluate_all_reply_envelope(
        authority_rows,
        envelope_id=envelope_id,
        generic_seed=int(generic_seed),
    )
    selected_id = envelope.counterexample_reply_id
    selected = next(
        (context for context in contexts if context["reply_id"] == selected_id),
        None,
    )
    if selected is None:
        raise RuntimeError("all-reply envelope selected no enumerated reply")
    provider_ids = tuple(sorted({
        str(context["provider_id"])
        for context in contexts
        if context["effective_available"]
        and isinstance(context.get("provider_id"), str)
        and context["provider_id"]
    }))
    provider_records: dict[str, dict[str, Any]] = {}
    for context in contexts:
        record = context.get("provider_record")
        if (
            not context["effective_available"]
            or context.get("provider_kind") not in {
                "native_direct_outcome_cell",
                "prospective_authority_cell",
            }
            or not isinstance(record, Mapping)
        ):
            continue
        provider_id = str(record.get("cell_id", ""))
        if not provider_id:
            raise RuntimeError("available shell provider lacks an identity")
        normalized = dict(record)
        prior = provider_records.get(provider_id)
        if prior is not None and prior != normalized:
            raise RuntimeError(
                "shell provider changed during one read-only envelope"
            )
        provider_records[provider_id] = normalized
    return {
        "envelope": envelope,
        "contexts": tuple(contexts),
        "selected": selected,
        "virtual_query_count": virtual_query_count,
        "terminal_refuted_count": terminal_refuted_count,
        "reply_ids": tuple(context["reply_id"] for context in contexts),
        "selected_exposure_key": selected["exposure_key"],
        "provider_ids": provider_ids,
        "provider_records": provider_records,
    }


def _prospective_counterexample_episode(
    authority: Any,
    after_first: chess.Board,
    *,
    credit: IntrinsicCreditEngine | None = None,
    decision_id: str | None = None,
    fen: str,
    white_move_uci: str,
    arm_name: str,
    epoch: int,
    position_index: int,
    exposure_counts: dict[tuple[str, str, str], int],
    seen_predecessor_fens: set[str],
    frame_session: Any | None,
    generic_seed: int,
    arm_bootstrap_enabled: bool,
    counters: dict[str, int | float],
    strict_adaptive: bool = False,
    boundary_ecology: ProspectiveBoundaryCandidateEcology | None = None,
    pending_boundary_candidate_ids: set[str] | None = None,
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
) -> tuple[str | None, tuple[str, ...], dict[str, Any]]:
    """Run the one selected REAL successor after an all-reply VIRTUAL probe."""

    if strict_adaptive:
        # In the native path the persisted episode counter is the causal
        # interaction ordinal.  Epoch/position are presentation metadata and
        # must not enter receipt, ecology-incarnation, or authority IDs: a
        # resumed/chunked stream with the same REAL interactions must replay
        # the same organism.  Strict callers must provide the persisted
        # counter explicitly: silently collapsing an omitted counter to zero
        # would alias distinct interactions and invalidate replay identity.
        if "episodes" not in counters:
            raise ValueError(
                "strict adaptive REAL frame identity requires explicit "
                "counters['episodes']"
            )
        interaction_ordinal = counters["episodes"]
        if (
            isinstance(interaction_ordinal, bool)
            or not isinstance(interaction_ordinal, int)
            or interaction_ordinal < 0
        ):
            raise ValueError(
                "strict adaptive REAL frame identity requires "
                "counters['episodes'] to be a nonnegative integer"
            )
        frame_prefix = (
            f"native-intrinsic-v2:{arm_name}:interaction:{interaction_ordinal}:"
            f"{white_move_uci}"
        )
    else:
        frame_prefix = (
            f"native-intrinsic-v2:{arm_name}:{epoch}:{position_index}:"
            f"{white_move_uci}"
        )
    probe = _prospective_counterexample_reply_probe(
        authority,
        after_first,
        fen=fen,
        white_move_uci=white_move_uci,
        exposure_counts=exposure_counts,
        frame_prefix=frame_prefix,
        frame_session=frame_session,
        generic_seed=generic_seed,
        strict_adaptive=strict_adaptive,
        r0_core_graph=r0_core_graph,
        r0_core_gate=r0_core_gate,
        r0_core_triplet_ids=r0_core_triplet_ids,
    )
    envelope = probe["envelope"]
    selected = probe["selected"]
    counters["reply_envelope_count"] += 1
    counters["reply_envelope_available_count"] += int(
        envelope.state is AvailabilityState.AVAILABLE
    )
    counters["reply_envelope_unknown_count"] += int(
        envelope.state is AvailabilityState.UNKNOWN
    )
    counters["reply_envelope_refuted_count"] += int(
        envelope.state is AvailabilityState.REFUTED
    )
    counters["reply_envelope_positive_count"] += int(envelope.positive_gate)
    counters["reply_virtual_query_count"] += probe["virtual_query_count"]
    counters["reply_terminal_refuted_count"] += probe["terminal_refuted_count"]
    counters["availability_queries"] += probe["virtual_query_count"]
    counters["availability_positives"] += sum(
        int(row.state is AvailabilityState.AVAILABLE and row.grounded)
        for row in envelope.replies
    )
    counters["virtual_frame_queries"] += probe["virtual_query_count"]
    selected_exposure_key = probe["selected_exposure_key"]
    exposure_count = int(exposure_counts.get(selected_exposure_key, 0))
    reply_orbits = (selected_exposure_key,)
    selected_successor = selected["successor"]
    selected_terminal_kind = selected["terminal_kind"]
    counters["reply_counterexample_count"] += 1
    structural: dict[str, Any] | None = None
    real_event = False
    actual_mate = False
    successor_signal: CompetenceSignal | None = None
    successor_signal_evidence: str | None = None
    false_authority_ids: tuple[str, ...] = ()
    # The all-reply selector may deliberately choose a terminal black reply
    # (REFUTED).  Keep effective-routing fields initialized so that this
    # fail-closed branch still produces a complete event manifest.
    available = False
    effective_core_available = False
    effective_available = False
    selected_provider_identity_parity = False
    core_routing: dict[str, Any] = {}
    response: dict[str, Any] = {
        "selected_move": None,
        "selected_triplet": None,
        "observed_immediate_mate": False,
        "classification": selected["classification"],
        "certification_emission": None,
    }
    if selected_terminal_kind is not None:
        # A terminal black reply is already a failed continuation for R1; it
        # must not be interpreted as a positive child event.
        terminal_kind = _r1_terminal_reply_terminal_kind(selected_terminal_kind)
    else:
        expected_virtual = selected.get("v2_response")
        if not isinstance(expected_virtual, Mapping):
            raise RuntimeError(
                "nonterminal all-reply selection omitted VIRTUAL actuation"
            )
        virtual_move_uci = expected_virtual.get("selected_move")
        preflight_actual_mate = False
        if isinstance(virtual_move_uci, str) and virtual_move_uci:
            virtual_move = chess.Move.from_uci(virtual_move_uci)
            if virtual_move not in selected_successor.legal_moves:
                raise RuntimeError(
                    "VIRTUAL child emitted an illegal selected action"
                )
            preflight_actual_mate = bool(
                _execute_white_and_observe(
                    selected_successor,
                    virtual_move,
                )
                == "mate"
            )
        selected_provider_id = selected.get("provider_id")
        virtual_provider_id = expected_virtual.get("provider_id")
        preflight_provider_parity = bool(
            isinstance(selected_provider_id, str)
            and selected_provider_id
            and selected_provider_id == virtual_provider_id
        )
        preflight_successor_signal = _grounded_all_reply_successor_signal(
            envelope,
            bootstrap_enabled=arm_bootstrap_enabled,
            actual_mate=preflight_actual_mate,
            clean_preoutcome_evidence=bool(
                preflight_provider_parity
                and selected.get("effective_available") is True
            ),
            credit=credit,
            provider_ids=probe["provider_ids"],
            provider_records=probe["provider_records"],
            external_provider_resolver=getattr(
                authority,
                "native_provider_response",
                None,
            ),
            strict_adaptive=strict_adaptive,
        )
        if preflight_successor_signal is not None:
            if credit is None or decision_id is None:
                if strict_adaptive:
                    raise RuntimeError(
                        "strict handoff preflight lacks its recipient credit cell"
                    )
            else:
                credit.preflight_explicit_successor_signal(
                    preflight_successor_signal,
                    recipient_id=decision_id,
                    external_provider_records=probe["provider_records"],
                    external_provider_resolver=getattr(
                        authority,
                        "native_provider_response",
                        None,
                    ),
                )
        available, response, duplicate, structural = (
            _v2_r0_observe_training_successor(
                authority,
                selected_successor,
                seen_predecessor_fens=seen_predecessor_fens,
                frame_id=f"{frame_prefix}:selected:{selected['black_move']}",
                frame_session=frame_session,
                expected_virtual_actuation=selected.get("v2_response"),
                boundary_ecology=boundary_ecology,
                pending_boundary_candidate_ids=pending_boundary_candidate_ids,
                r0_core_graph=r0_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=r0_core_triplet_ids,
            )
        )
        real_event = not duplicate
        counters["reply_counterexample_real_event_count"] += int(real_event)
        counters["reply_counterexample_duplicate_virtual_count"] += int(duplicate)
        counters["v2_duplicate_virtual_queries"] += int(duplicate)
        counters["v2_real_observations"] += int(real_event)
        actual_mate = bool(response.get("observed_immediate_mate", False))
        core_routing = response.get("core_routing") or {}
        effective_core_available = bool(
            core_routing.get("available", False)
        )
        effective_available = bool(
            core_routing.get("effective_available", available)
        )
        selected_provider_id = selected.get("provider_id")
        real_provider_id = response.get("provider_id")
        selected_provider_identity_parity = bool(
            (
                isinstance(selected_provider_id, str)
                and selected_provider_id
                and selected_provider_id == real_provider_id
            )
            or (
                not strict_adaptive
                and selected_provider_id is None
                and real_provider_id is None
            )
        )
        emission = response.get("certification_emission") or {}
        false_authority_ids = tuple(
            str(item)
            for item in emission.get("prequential_false_authority_ids", ())
        )
        counters["reply_counterexample_false_authority_count"] += int(
            bool(false_authority_ids)
        )
        if actual_mate:
            counters["reply_counterexample_mate_count"] += 1
        elif real_event:
            counters["reply_counterexample_failure_count"] += 1
        if actual_mate and not envelope.positive_gate:
            counters["reply_counterexample_surprise_success_count"] += 1
        clean_preoutcome_evidence = bool(
            selected_provider_identity_parity and (
                (real_event or duplicate)
                if effective_core_available
                else (
                    ((real_event or duplicate) and not false_authority_ids)
                    and effective_available
                )
            )
        )
        successor_signal = _grounded_all_reply_successor_signal(
            envelope,
            bootstrap_enabled=arm_bootstrap_enabled,
            actual_mate=actual_mate,
            clean_preoutcome_evidence=clean_preoutcome_evidence,
            credit=credit,
            provider_ids=probe["provider_ids"],
            provider_records=probe["provider_records"],
            external_provider_resolver=getattr(
                authority,
                "native_provider_response",
                None,
            ),
            strict_adaptive=strict_adaptive,
        )
        if (
            strict_adaptive
            and successor_signal is not None
            and successor_signal != preflight_successor_signal
        ):
            raise RuntimeError(
                "post-REAL successor signal diverged from preflight"
            )
        if successor_signal is not None:
            counters["reply_counterexample_handoff_count"] += 1
            counters["child_handoffs"] += 1
            successor_ids = tuple(successor_signal.provider_ids)
            successor_signal_evidence = (
                "fresh_preoutcome_envelope"
                if real_event
                else "reused_prior_real_evidence"
            )
        else:
            successor_ids = ()
        # Keep two kinds of learning evidence separate.  A provider-backed
        # all-reply signal is prospective value and must not also receive a
        # terminal reward.  Without such a signal, an actually observed mate
        # is still an ordinary environmental return for the exact R1 action;
        # suppressing it would train successful behavior as failure.  This
        # terminal credit neither creates a provider nor counts as shell
        # certification, and duplicate authority evidence remains excluded.
        terminal_kind = (
            None
            if successor_signal is not None
            else ("mate" if actual_mate else "horizon")
        )
    if selected_terminal_kind is not None:
        successor_ids = ()
    # Commit local challenge exposure only after the complete event path has
    # returned successfully.  A precommit actuation/parity failure must be a
    # read-only rejection, not a hidden change in future reply selection.
    exposure_counts[selected_exposure_key] = exposure_count + 1
    if structural is not None:
        counters["v2_structural_transitions"] += 1
    event_manifest = {
        "fen": str(fen),
        "white_move": str(white_move_uci),
        "reply_ids": list(probe["reply_ids"]),
        "selected_reply_id": selected["reply_id"],
        "selected_black_move": selected["black_move"],
        "selected_terminal_kind": selected_terminal_kind,
        "provider_ids": list(probe["provider_ids"]),
        "local_provider_ids": list(probe["provider_ids"]),
        "external_provider_records": {
            key: dict(value)
            for key, value in sorted(probe["provider_records"].items())
        },
        "envelope": envelope.audit.to_manifest(),
        "reply_context": [
            {
                "reply_id": context["reply_id"],
                "black_move": context["black_move"],
                "terminal_kind": context["terminal_kind"],
                "classification": context["classification"],
                "v2_available": context["v2_available"],
                "v2_grounding": context["v2_grounding"],
                "core_available": context["core_available"],
                "effective_core_available": context[
                    "effective_core_available"
                ],
                "effective_available": context["effective_available"],
                "effective_source": context["effective_source"],
                "provider_id": context["provider_id"],
                "provider_kind": context["provider_kind"],
                "authority_row": context["authority_row"].to_manifest(),
                "exposure_count": context["exposure_count"],
            }
            for context in probe["contexts"]
        ],
        "real_event": real_event,
        "duplicate_virtual_query": bool(not real_event and selected_terminal_kind is None),
        "actual_r0_action_mated": actual_mate,
        "raw_v2_available": bool(available),
        "effective_core_available": effective_core_available,
        "effective_reply_available": effective_available,
        "selected_provider_identity_parity": (
            selected_provider_identity_parity
        ),
        "effective_source": (
            str(core_routing.get("effective_source"))
            if selected_terminal_kind is None and core_routing
            else (
                "v2_grounded_descendant"
                if selected_terminal_kind is None and available
                else (
                    "terminal_refuted"
                    if selected_terminal_kind is not None
                    else "unknown"
                )
            )
        ),
        "core_overrode_v2_false_authority": bool(
            effective_core_available and false_authority_ids
        ),
        "prequential_false_authority_ids": list(false_authority_ids),
        "positive_handoff": bool(successor_ids),
        "retrospective_environmental_mate_credit": bool(
            terminal_kind == "mate" and not successor_ids
        ),
        "successor_signal": (
            None
            if successor_signal is None
            else {
                "value": successor_signal.value,
                "confidence": successor_signal.confidence,
                "provider_ids": list(successor_signal.provider_ids),
                "grounding_level": successor_signal.grounding_level,
                "grounding_ancestors": list(
                    successor_signal.grounding_ancestors
                ),
                "evidence": successor_signal_evidence,
                "aggregation": "minimum_over_all_grounded_available_replies",
            }
        ),
    }
    return terminal_kind, successor_ids, {
        "manifest": event_manifest,
        "reply_orbits": tuple(reply_orbits),
        "structural": structural,
        "response": response,
        "selected_exposure_key": selected_exposure_key,
        "successor_signal": successor_signal,
        "external_provider_records": probe["provider_records"],
    }


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
        payload = {"schema_version": "krk_native_intrinsic_r0_r1_progress.v1"}
    payload["schema_version"] = "krk_native_intrinsic_r0_r1_progress.v1"
    # A resumed/ reused progress file may have been written by the pre-purity
    # runner.  Remove its stale R0 regression value before publishing a live
    # checkpoint; completed-arm summaries are final-report data and are left
    # untouched.
    r0_progress = payload.get("r0")
    if isinstance(r0_progress, dict):
        r0_progress.pop("regression_accuracy", None)
    payload["active_r1_arm"] = {
        "arm_name": arm_name,
        "epoch": int(epoch),
        "validation_conversion_rate": checkpoint.get("validation_conversion_rate"),
        "r0_retention_accuracy": checkpoint.get("r0_retention_accuracy"),
        "r0_validation_retention_accuracy": checkpoint.get(
            "r0_validation_retention_accuracy"
        ),
        "r0_validation_retention_metric": checkpoint.get(
            "r0_validation_retention_metric"
        ),
        "r0_validation_retention_semantics": checkpoint.get(
            "r0_validation_retention_semantics"
        ),
        "r0_frozen_native_policy_retention_accuracy": checkpoint.get(
            "r0_frozen_native_policy_retention_accuracy"
        ),
        "r0_v2_shell_coverage_accuracy": checkpoint.get(
            "r0_v2_shell_coverage_accuracy"
        ),
        "regression_withheld_until_final": True,
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


def _attach_terminal_r1_regression_report(
    arm: dict[str, Any],
    pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
) -> None:
    """Attach one arm's withheld reports after all arms have trained.

    R1 arms are allowed to finish with validation metrics only.  The private
    context is deliberately kept out of JSON and carries the exact mutated
    graph plus the read-only child-routing inputs needed for the terminal
    measurements.  Keeping this assembly separate from ``_run_r1_arm`` makes
    it impossible for the full arm's held-out result to be read while the
    control arm is still training in the top-level runner.

    A preassembled arm is accepted for compatibility with lightweight test
    doubles and older callers that invoke ``_run_r1_arm`` themselves.  Real
    deferred arms always carry the context and therefore execute exactly one
    R1-regression and one R0-regression-retention query here.
    """

    context = arm.pop("_terminal_regression_context", None)
    if context is None:
        if (
            arm.get("regression") is not None
            and arm.get("r0_regression_retention") is not None
        ):
            return
        raise RuntimeError(
            "deferred R1 arm omitted terminal regression evaluation context"
        )

    graph = context["graph"]
    core_graph = context.get("r0_core_graph")
    core_gate = context.get("r0_core_gate")
    core_triplet_ids = context.get("r0_core_triplet_ids")
    heldout_disabled_state = _disable_nonmature_composites(
        graph,
        enabled=config.r1_heldout_mature_composites_only,
    )
    try:
        final_regression = _evaluate_r1(
            graph,
            pools.r1_regression,
            strata=pools.r1_regression_strata,
            max_samples=config.max_samples,
            r0_child_triplet_ids=context["r0_child_triplet_ids"],
            child_dispatch_cache=context["child_dispatch_cache"],
            r0_child_authority=context["r0_child_authority"],
            r0_core_graph=core_graph,
            r0_core_gate=core_gate,
            r0_core_triplet_ids=core_triplet_ids,
            action_selection_mode=config.r1_action_selection_mode,
        )
        final_r0_regression_retention = _evaluate_r0(
            graph,
            pools.r0_regression,
            max_samples=config.max_samples,
            r0_child_triplet_ids=context["r0_child_triplet_ids"],
            child_dispatch_cache=context["child_dispatch_cache"],
            r0_child_authority=context["r0_child_authority"],
            r0_core_graph=core_graph,
            r0_core_gate=core_gate,
            r0_core_triplet_ids=core_triplet_ids,
            allow_frozen_core=(core_graph is not None and core_gate is not None),
            action_selection_mode=config.r1_action_selection_mode,
        )
        v2_shell_coverage_active = bool(
            context["r0_child_authority"] is not None
            and config.r1_action_selection_mode
            == R1_ACTION_SELECTION_LOCAL_RECON
        )
        final_r0_regression_retention = _annotate_r0_metric(
            final_r0_regression_retention,
            metric_name=(
                "r0_v2_shell_coverage"
                if v2_shell_coverage_active
                else "r0_regression_retention"
            ),
            metric_semantics=(
                "native_v2_shell_available_mate_coverage;"
                "not_frozen_graph_retention"
                if v2_shell_coverage_active
                else "regression_retention_for_current_legacy_routing"
            ),
            source=(
                "native_v2_authority_graph_emission"
                if v2_shell_coverage_active
                else "current_r1_routing"
            ),
            compatibility_key="r0_regression_retention",
        )
    finally:
        _restore_disabled_composites(graph, heldout_disabled_state)

    final_regression_pass_report_only = bool(
        final_regression["conversion_rate"] >= config.r1_mastery_threshold
        and final_r0_regression_retention["accuracy"]
        >= config.r0_mastery_threshold
    )
    arm["regression"] = final_regression
    arm["r0_retention"] = final_r0_regression_retention
    arm["r0_regression_retention"] = final_r0_regression_retention
    if (
        context["r0_child_authority"] is not None
        and config.r1_action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
    ):
        arm["r0_v2_shell_regression_coverage"] = (
            final_r0_regression_retention
        )
    arm["regression_withheld_until_final"] = True
    arm["regression_pass_report_only"] = final_regression_pass_report_only
    routing_ablation = arm.get("routing_ablation")
    current_routing_name = context["current_routing_name"]
    if isinstance(routing_ablation, dict):
        current_routing = routing_ablation.get(current_routing_name)
        if isinstance(current_routing, dict):
            current_routing["regression"] = final_regression
            current_routing.pop("regression_withheld_from_routing_ablation", None)
    arm["terminal_regression_evaluation"] = {
        "evaluated_after_all_r1_arms": True,
        "r1_regression_query_count": 1,
        "r0_regression_retention_query_count": 1,
        "selection_influenced": False,
    }


def _run_r1_arm(
    arm_name: str,
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    r0_gate: OutcomeCalibratedPrototypeGate | None,
    pools: _Pools,
    *,
    r0_replay_memory: Sequence[_R0ReplayExperience],
    r0_child_triplet_ids: frozenset[str],
    max_epochs: int,
    config: NativeIntrinsicCurriculumConfig,
    stop_after_epoch: int | None = None,
    arm_spec: R1MechanisticArm | None = None,
    r0_child_authority: Any | None = None,
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
    run_started: float | None = None,
    defer_regression_evaluation: bool = False,
) -> dict[str, Any]:
    arm = arm_spec or _legacy_r1_arm(arm_name, config)
    strict_adaptive = _strict_local_adaptive_mode(config)
    if arm.name != arm_name:
        raise ValueError(f"arm name mismatch: {arm.name} != {arm_name}")
    # Capture the pre-R1 source before the arm graph is mutated.  Adaptive V2
    # replaces this with the authority-owned immutable source below; legacy
    # arms retain this isolated post-R0 copy for explicit policy retention.
    initial_frozen_native_policy_graph = copy.deepcopy(
        r0_core_graph if r0_core_graph is not None else graph
    )
    graph.config = replace(
        graph.config,
        score_hierarchy_edge_weights=arm.hierarchy_edge_scoring,
    )
    # Keep an explicitly supplied core copy for legacy/non-V2 callers.  A V2
    # arm instead reuses the immutable R0 source inside its cloned authority;
    # copying it here would create a second shadow graph per arm.
    supplied_core_graph = r0_core_graph
    supplied_core_triplet_ids = (
        None
        if r0_core_triplet_ids is None
        else frozenset(r0_core_triplet_ids)
    )
    if r0_child_authority is None:
        if r0_core_graph is not None:
            r0_core_graph = copy.deepcopy(r0_core_graph)
            r0_core_triplet_ids = (
                frozenset(r0_core_graph.triplet_ids)
                if r0_core_triplet_ids is None
                else supplied_core_triplet_ids
            )
            if not r0_core_triplet_ids.issubset(r0_core_graph.triplet_ids):
                raise ValueError(
                    "protected R0 core triplet ids are not in its graph"
                )
        elif r0_core_gate is not None or r0_core_triplet_ids:
            raise ValueError(
                "protected core gate/triplet ids require a protected core graph"
            )
    child_value_control = _apply_child_value_control(credit, arm, config)
    if r0_child_authority is not None:
        authority_type = type(r0_child_authority)
        r0_child_authority = authority_type.loads(r0_child_authority.dumps())
        if r0_child_authority.pending_event is not None:
            raise RuntimeError("R1 child authority clone has a pending REAL event")
        authority_r0 = getattr(
            getattr(r0_child_authority, "base", None), "r0", None
        )
        authority_graph = getattr(authority_r0, "graph", None)
        authority_triplets = getattr(authority_r0, "frozen_triplet_ids", None)
        if (
            r0_core_gate is not None
            and authority_graph is not None
            and authority_triplets is not None
        ):
            if supplied_core_graph is not None and _hash_json(
                supplied_core_graph.canonical_semantic_manifest()
            ) != _hash_json(authority_graph.canonical_semantic_manifest()):
                raise RuntimeError(
                    "explicit protected core differs from V2 authority R0 source"
                )
            if (
                supplied_core_triplet_ids is not None
                and supplied_core_triplet_ids != frozenset(authority_triplets)
            ):
                raise RuntimeError(
                    "explicit protected core IDs differ from V2 authority R0 source"
                )
            r0_core_graph = authority_graph
            r0_core_triplet_ids = frozenset(authority_triplets)
        elif r0_core_gate is not None and r0_core_graph is None and (
            r0_core_gate is not None or r0_core_triplet_ids
        ):
            raise TypeError(
                "V2 child authority does not expose its immutable R0 organism"
            )
        if r0_core_gate is None:
            # Native V2 authority already owns and binds its immutable R0
            # source.  Do not expose that graph as a second, host-routed core.
            r0_core_graph = None
            r0_core_triplet_ids = None
        if r0_core_graph is not None and r0_core_triplet_ids is None:
            r0_core_triplet_ids = frozenset(r0_core_graph.triplet_ids)
        if r0_core_graph is not None and not r0_core_triplet_ids.issubset(
            r0_core_graph.triplet_ids
        ):
            raise ValueError("protected R0 core triplet ids are not in its graph")
    frozen_native_policy_graph = (
        _copy_frozen_native_r0_graph(
            graph,
            r0_child_authority=r0_child_authority,
            r0_core_graph=r0_core_graph,
        )
        if r0_child_authority is not None
        else initial_frozen_native_policy_graph
    )
    boundary_ecology: ProspectiveBoundaryCandidateEcology | None = None
    if config.r0_boundary_ecology_enabled:
        if r0_child_authority is None:
            raise ValueError("boundary ecology requires a V2 child authority")
        if StructuralMode(r0_child_authority.structural_mode) is not (
            StructuralMode.EVENT_DRIVEN
        ):
            raise ValueError(
                "boundary ecology requires event-driven structural authority"
            )
        boundary_ecology = _new_boundary_ecology_from_authority_history(
            r0_child_authority,
            genome_seed=int(config.seed),
        )
    effective_reply_policy = _effective_r1_reply_policy(
        config, r0_child_authority
    )
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
        r0_core_graph=r0_core_graph,
        r0_core_triplet_ids=r0_core_triplet_ids,
    )
    protected_core_identity = (
        {
            # The V2 authority payload/continuation digest already binds its
            # immutable R0 graph, frozen IDs, and provenance.  Only retain a
            # source marker here; the gate remains part of the fingerprint.
            "source": "authority.base.r0",
        }
        if r0_child_authority is not None
        else {
            "graph_semantic_state_sha256": (
                None
                if r0_core_graph is None
                else _hash_json(r0_core_graph.canonical_semantic_manifest())
            ),
            "triplet_ids": sorted(r0_core_triplet_ids or ()),
            "gate": None if r0_core_gate is None else r0_core_gate.to_dict(),
        }
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
    restored_shuffled_schedule: tuple[bool, ...] = ()
    restored_shuffled_schedule_audit: Mapping[str, Any] | None = None
    if restored is None:
        credit.register(R1_COMPETENCE_ID, mature=False, hierarchy_depth=0)
        start_epoch = 0
        counters = {
            "episodes": 0,
            "local_action_first_contact_selections": 0,
            "local_action_post_contact_selections": 0,
            "local_action_exact_q_selections": 0,
            "local_action_positive_credit_revisits": 0,
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
            "reply_envelope_count": 0,
            "reply_envelope_available_count": 0,
            "reply_envelope_unknown_count": 0,
            "reply_envelope_refuted_count": 0,
            "reply_envelope_positive_count": 0,
            "reply_virtual_query_count": 0,
            "reply_terminal_refuted_count": 0,
            "reply_counterexample_count": 0,
            "reply_counterexample_real_event_count": 0,
            "reply_counterexample_duplicate_virtual_count": 0,
            "reply_counterexample_mate_count": 0,
            "reply_counterexample_failure_count": 0,
            "reply_counterexample_surprise_success_count": 0,
            "reply_counterexample_false_authority_count": 0,
            "reply_counterexample_handoff_count": 0,
        }
        reply_orbits: set[tuple[str, str, str]] = set()
        reply_exposure_counts: dict[tuple[str, str], int] = {}
        reply_exposure_counts_by_reply: dict[tuple[str, str, str], int] = {}
        child_dispatch_cache: dict[str, dict[str, Any]] = {}
        checkpoints: list[dict[str, Any]] = []
        composition_events: list[dict[str, Any]] = []
        composition_consolidation_events: list[dict[str, Any]] = []
        v2_structural_events: list[dict[str, Any]] = []
        reply_policy_events: list[dict[str, Any]] = []
        reply_policy_event_digest = _hash_json({
            "schema": "native_intrinsic_r1_reply_policy_events.v1",
            "events": [],
        })
        local_action_events: list[dict[str, Any]] = []
        # Report-only evidence for the finite mechanism gate.  This set never
        # enters action competition, authority, reward, or candidate growth.
        local_action_positive_credit_options: set[tuple[str, str]] = set()
        local_action_event_digest = _hash_json({
            "schema": "native_intrinsic_r1_local_action_events.v1",
            "events": [],
        })
        history_snapshot_paths: list[str] = []
        stopped_epoch = epoch_budget
        joint_mastery = False
    else:
        persisted_core_identity = restored.get("r0_core_routing")
        if r0_core_graph is not None and persisted_core_identity != protected_core_identity:
            raise RuntimeError(
                "R1 snapshot protected R0 core routing identity mismatch"
            )
        saved_budget = int(restored["epoch_budget"])
        if saved_budget != epoch_budget:
            raise ValueError(
                f"R1 snapshot epoch budget mismatch: {saved_budget} != {epoch_budget}"
            )
        saved_policy = str(
            restored.get(
                "reply_policy", R1_REPLY_POLICY_SAMPLED_ROUND_ROBIN
            )
        )
        if saved_policy != effective_reply_policy:
            raise ValueError(
                "R1 snapshot reply policy mismatch: "
                f"{saved_policy} != {effective_reply_policy}"
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
            # The serialized authority is the source of truth after resume.
            # Rebind the routing aliases immediately; retaining the pre-load
            # authority graph would make later no-frame queries use a stale
            # object and bypass the authority's isolated dream session.
            restored_r0 = getattr(
                getattr(r0_child_authority, "base", None), "r0", None
            )
            restored_graph = getattr(restored_r0, "graph", None)
            restored_triplets = getattr(
                restored_r0, "frozen_triplet_ids", None
            )
            core_routing_requested = bool(
                r0_core_graph is not None
                or r0_core_gate is not None
                or r0_core_triplet_ids
            )
            if (
                core_routing_requested
                and (restored_graph is None or restored_triplets is None)
            ):
                raise RuntimeError(
                    "restored V2 authority does not expose its immutable R0 organism"
                )
            if (
                core_routing_requested
                and restored_graph is not None
                and restored_triplets is not None
            ):
                r0_core_graph = restored_graph
                r0_core_triplet_ids = frozenset(restored_triplets)
                if not r0_core_triplet_ids.issubset(r0_core_graph.triplet_ids):
                    raise RuntimeError(
                        "restored V2 authority R0 IDs are not in its source graph"
                    )
            elif not core_routing_requested:
                r0_core_graph = None
                r0_core_triplet_ids = None
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
            ecology_manifest = restored.get("boundary_ecology_manifest")
            if config.r0_boundary_ecology_enabled:
                if not isinstance(ecology_manifest, Mapping):
                    raise RuntimeError(
                        "adaptive R1 snapshot omitted boundary ecology state"
                    )
                boundary_ecology = (
                    ProspectiveBoundaryCandidateEcology.from_manifest(
                        ecology_manifest
                    )
                )
                _verify_boundary_ecology_alignment(
                    r0_child_authority,
                    boundary_ecology,
                    roundtrip=True,
                )
            elif ecology_manifest is not None:
                raise RuntimeError(
                    "non-adaptive R1 snapshot contains boundary ecology state"
                )
        elif authority_payload is not None:
            raise RuntimeError("legacy R1 arm snapshot contains V2 authority state")
        start_epoch = int(restored["next_epoch"])
        counters = dict(restored["counters"])
        for key in (
            "local_action_first_contact_selections",
            "local_action_post_contact_selections",
            "local_action_exact_q_selections",
            "local_action_positive_credit_revisits",
        ):
            counters.setdefault(key, 0)
        for key, default in _r1_reply_counter_defaults().items():
            counters.setdefault(key, default)
        reply_orbits = set(restored["reply_orbits"])
        reply_exposure_counts = dict(restored["reply_exposure_counts"])
        reply_exposure_counts_by_reply = dict(
            restored.get("reply_exposure_counts_by_reply", {})
        )
        child_dispatch_cache = dict(restored["child_dispatch_cache"])
        checkpoints = list(restored["checkpoints"])
        composition_events = list(restored.get("composition_events", []))
        composition_consolidation_events = list(
            restored.get("composition_consolidation_events", [])
        )
        v2_structural_events = list(restored.get("v2_structural_events", []))
        reply_policy_events = list(restored.get("reply_policy_events", []))[-16:]
        reply_policy_event_digest = str(
            restored.get(
                "reply_policy_event_digest",
                _hash_json({
                    "schema": "native_intrinsic_r1_reply_policy_events.v1",
                    "events": [],
                }),
            )
        )
        local_action_events = list(
            restored.get("local_action_events", [])
        )[-16:]
        local_action_positive_credit_options = set(
            tuple(item)
            for item in restored.get("local_action_positive_credit_options", ())
        )
        local_action_event_digest = str(
            restored.get(
                "local_action_event_digest",
                _hash_json({
                    "schema": "native_intrinsic_r1_local_action_events.v1",
                    "events": [],
                }),
            )
        )
        history_snapshot_paths = list(restored.get("history_snapshot_paths", []))
        stopped_epoch = int(restored["stopped_epoch"])
        joint_mastery = bool(restored["joint_mastery"])
        duration_before_resume = float(restored["duration_seconds"])
        snapshot_writes = int(restored.get("snapshot_writes", 0))
        restored_shuffled_schedule = tuple(
            bool(item) for item in restored.get("shuffled_schedule", ())
        )
        restored_shuffled_schedule_audit = restored.get(
            "shuffled_schedule_audit"
        )

    # A mastery snapshot is already a complete validation-selected arm.  A
    # resume must only reconstruct its report; replaying from ``next_epoch``
    # would silently train beyond the committed stopping point and make the
    # resumed result diverge from an uninterrupted completion.
    resumed_from_mastered_snapshot = bool(restored is not None and joint_mastery)

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
    if resumed_from_mastered_snapshot:
        # The schedule is an operational artifact, not a reason to reopen a
        # mastered arm.  Reuse the committed copy when present so the report
        # remains identical without re-probing the graph.
        shuffled_schedule = restored_shuffled_schedule
        if isinstance(restored_shuffled_schedule_audit, Mapping):
            shuffled_schedule_audit = dict(restored_shuffled_schedule_audit)
        elif arm.availability_mode == "shuffled_prototype_gate":
            shuffled_schedule_audit = {
                "enabled": True,
                "restored_mastery_snapshot": True,
                "schedule_not_persisted": True,
            }
    elif arm.availability_mode == "shuffled_prototype_gate":
        shuffled_schedule, shuffled_schedule_audit = _shuffled_gate_schedule(
            r0_core_graph if r0_core_graph is not None else graph,
            r0_core_gate if r0_core_gate is not None else r0_gate,
            pools,
            r0_child_triplet_ids=r0_child_triplet_ids,
            epoch_budget=epoch_budget,
            seed=config.r1_shuffle_seed,
        )
        shuffled_schedule_audit = {
            "enabled": True,
            **shuffled_schedule_audit,
        }

    epoch_iterator = (
        ()
        if resumed_from_mastered_snapshot
        else range(start_epoch, epoch_budget)
    )
    for epoch in epoch_iterator:
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
                (
                    move,
                    triplet_id,
                    confirmed,
                    graph_prediction,
                    local_action_manifest,
                ) = _select_r1_training_action(
                    graph,
                    board,
                    epoch=epoch,
                    position_index=position_index,
                    fen=fen,
                    config=config,
                )
                counters["formal_confirmation_failures"] += int(not confirmed)
                after_first = board.copy(stack=False)
                after_first.push(move)
                terminal_kind: str | None = _terminal_kind(after_first)
                successor_ids: tuple[str, ...] = ()
                explicit_successor_signal: CompetenceSignal | None = None
                external_provider_records: dict[
                    str, Mapping[str, Any]
                ] = {}
                # Keep structural work born by this decision pending until
                # the exact all-reply value has crossed credit and graph TD.
                # This set is deliberately per interaction (never per epoch):
                # a capacity retirement triggered by the new bud must not
                # revoke a provider that the current handoff still needs.
                pending_boundary_candidate_ids: set[str] | None = (
                    set()
                    if (
                        r0_child_authority is not None
                        and StructuralMode(
                            getattr(
                                r0_child_authority,
                                "structural_mode",
                                StructuralMode.SCHEDULED,
                            )
                        )
                        is StructuralMode.EVENT_DRIVEN
                    )
                    else None
                )
                unique_real_event = False
                reply_audit: dict[str, Any] | None = None
                if terminal_kind is None:
                    replies = tuple(sorted(after_first.legal_moves, key=lambda item: item.uci()))
                    if not replies:
                        terminal_kind = "failure"
                    elif effective_reply_policy == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE:
                        (
                            terminal_kind,
                            successor_ids,
                            reply_audit,
                        ) = _prospective_counterexample_episode(
                            r0_child_authority,
                            after_first,
                            credit=credit,
                            decision_id=triplet_id,
                            fen=fen,
                            white_move_uci=move.uci(),
                            arm_name=arm_name,
                            epoch=epoch,
                            position_index=position_index,
                            exposure_counts=reply_exposure_counts_by_reply,
                            seen_predecessor_fens=v2_seen_predecessor_fens,
                            frame_session=r0_frame_session,
                            generic_seed=config.seed,
                            arm_bootstrap_enabled=arm.bootstrap_enabled,
                            counters=counters,
                            strict_adaptive=strict_adaptive,
                            boundary_ecology=boundary_ecology,
                            pending_boundary_candidate_ids=(
                                pending_boundary_candidate_ids
                            ),
                            r0_core_graph=r0_core_graph,
                            r0_core_gate=r0_core_gate,
                            r0_core_triplet_ids=r0_core_triplet_ids,
                        )
                        reply_orbits.update(reply_audit["reply_orbits"])
                        explicit_successor_signal = reply_audit.get(
                            "successor_signal"
                        )
                        external_provider_records = dict(
                            reply_audit.get("external_provider_records", {})
                        )
                        unique_real_event = bool(
                            reply_audit["manifest"].get("real_event", False)
                        )
                        if (
                            pending_boundary_candidate_ids is None
                            and reply_audit["structural"] is not None
                        ):
                            v2_structural_events.append(
                                reply_audit["structural"]
                            )
                            if r0_frame_session is not None:
                                r0_frame_session.close()
                                r0_frame_session = r0_child_authority.frame_session()
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
                                    boundary_ecology=boundary_ecology,
                                    pending_boundary_candidate_ids=(
                                        pending_boundary_candidate_ids
                                    ),
                                    r0_core_graph=r0_core_graph,
                                    r0_core_gate=r0_core_gate,
                                    r0_core_triplet_ids=r0_core_triplet_ids,
                                )
                            )
                            counters["availability_queries"] += 1
                            counters["availability_positives"] += int(available)
                            counters["virtual_frame_queries"] += int(duplicate)
                            counters["v2_duplicate_virtual_queries"] += int(duplicate)
                            counters["v2_real_observations"] += int(not duplicate)
                            unique_real_event = bool(not duplicate)
                            if (
                                pending_boundary_candidate_ids is None
                                and structural is not None
                            ):
                                counters["v2_structural_transitions"] += 1
                                v2_structural_events.append(structural)
                                if r0_frame_session is not None:
                                    r0_frame_session.close()
                                    r0_frame_session = (
                                        r0_child_authority.frame_session()
                                    )
                            actual_child_mate = bool(
                                response.get("observed_immediate_mate", False)
                            )
                            core_routing = response.get("core_routing") or {}
                            effective_child_available = bool(
                                core_routing.get("effective_available", available)
                            )
                            effective_core_available = bool(
                                core_routing.get("available", False)
                            )
                            certification_emission = (
                                response.get("certification_emission") or {}
                            )
                            false_authority_ids = tuple(
                                certification_emission.get(
                                    "prequential_false_authority_ids", ()
                                )
                            )
                            if terminal_kind is None:
                                terminal_kind = (
                                    None if actual_child_mate else "horizon"
                                )
                            if (
                                arm.bootstrap_enabled
                                and effective_child_available
                                and actual_child_mate
                                and (
                                    effective_core_available
                                    or duplicate
                                    or not false_authority_ids
                                )
                            ):
                                if not strict_adaptive:
                                    successor_ids = (R0_COMPETENCE_ID,)
                                    counters["child_handoffs"] += 1
                        elif terminal_kind is None and arm.bootstrap_enabled:
                            available, response, cache_hit, cache_mismatch = (
                                _r0_available_with_dispatch_cache(
                                    (
                                        r0_core_graph
                                        if r0_core_graph is not None
                                        else graph
                                    ),
                                    (
                                        r0_core_gate
                                        if r0_core_gate is not None
                                        else r0_gate
                                    ),
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
                                    (
                                        r0_core_gate
                                        if r0_core_gate is not None
                                        else r0_gate
                                    ).confirms(response["features"])
                                )
                                response["availability_after_shuffle"] = bool(available)
                            counters["availability_queries"] += 1
                            counters["availability_positives"] += int(available)
                            if available and not strict_adaptive:
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
                    successor_ids=(
                        ()
                        if explicit_successor_signal is not None
                        else successor_ids
                    ),
                    explicit_successor_signal=explicit_successor_signal,
                    external_provider_records=(
                        external_provider_records
                        if explicit_successor_signal is not None
                        else None
                    ),
                    external_provider_resolver=(
                        getattr(
                            r0_child_authority,
                            "native_provider_response",
                            None,
                        )
                        if explicit_successor_signal is not None
                        else None
                    ),
                    terminal_kind=terminal_kind,
                    prediction_override=graph_prediction,
                )
                counters["successor_value_sum"] += float(event.successor_value)
                credited_triplet_id = graph.apply_intrinsic_td(
                    board,
                    move,
                    td_error=event.td_error,
                    stage_diagnostic="R1_mate_in_2",
                    prediction_value=(
                        graph_prediction
                        if local_action_manifest is not None
                        else None
                    ),
                )
                if credited_triplet_id != triplet_id:
                    raise RuntimeError(
                        "R1 TD credit diverged from the emitted action branch: "
                        f"{credited_triplet_id} != {triplet_id}"
                    )

                # In the native event-driven path, ecology/authority work is
                # deliberately split around the learner update.  The REAL
                # observation above may nominate a bud, but settling it can
                # retire a weak provider.  Waiting until both credit and graph
                # TD have returned keeps every provider used by this decision
                # alive through its complete all-reply value calculation.  A
                # duplicate VIRTUAL query and terminal-only outcome do not
                # open a structural transaction.
                settled_structural: dict[str, Any] | None = None
                if (
                    pending_boundary_candidate_ids is not None
                    and unique_real_event
                    and r0_child_authority is not None
                ):
                    settled_structural = _settle_event_local_v2_boundary(
                        r0_child_authority,
                        boundary_ecology,
                        pending_boundary_candidate_ids,
                    )
                    if settled_structural is not None:
                        counters["v2_structural_transitions"] += 1
                        v2_structural_events.append(settled_structural)
                        if reply_audit is not None:
                            reply_audit["structural"] = settled_structural
                        if r0_frame_session is not None:
                            r0_frame_session.close()
                            r0_frame_session = (
                                r0_child_authority.frame_session()
                            )

                # Keep the policy event report causally after the complete
                # decision.  In particular, a failed TD or structural commit
                # must not publish a receipt that the resumed report treats as
                # successfully settled.
                if reply_audit is not None:
                    reply_policy_event = reply_audit["manifest"]
                    reply_policy_events.append(reply_policy_event)
                    if len(reply_policy_events) > 16:
                        del reply_policy_events[:-16]
                    reply_policy_event_digest = _hash_json({
                        "prior": reply_policy_event_digest,
                        "event": reply_policy_event,
                    })
                if local_action_manifest is not None:
                    positive_credit_revisit = _record_r1_local_action_evidence(
                        local_action_manifest,
                        td_error=float(event.td_error),
                        terminal_kind=terminal_kind,
                        successor_value=float(event.successor_value),
                        counters=counters,
                        positive_credit_options=local_action_positive_credit_options,
                    )
                    action_event = {
                        **local_action_manifest,
                        "epoch": epoch + 1,
                        "position_index": position_index,
                        "credited_triplet_id": credited_triplet_id,
                        "td_error": float(event.td_error),
                        "successor_value": float(event.successor_value),
                        "terminal_kind": terminal_kind,
                        "positive_credited_exact_option_revisit": (
                            positive_credit_revisit
                        ),
                    }
                    local_action_events.append(action_event)
                    if len(local_action_events) > 16:
                        del local_action_events[:-16]
                    local_action_event_digest = _hash_json({
                        "prior": local_action_event_digest,
                        "event": action_event,
                    })
                counters["episodes"] += 1
                counters["failures"] += int(
                    terminal_kind not in (None, "mate")
                )
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
            frozen_core_graph=r0_core_graph,
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
                        r0_core_graph=r0_core_graph,
                        r0_core_gate=r0_core_gate,
                        r0_core_triplet_ids=r0_core_triplet_ids,
                        action_selection_mode=config.r1_action_selection_mode,
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
                r0_core_graph=r0_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=r0_core_triplet_ids,
                action_selection_mode=config.r1_action_selection_mode,
            )
            # R1 checkpoint selection retains the core against the independent
            # validation split only.  Never query R0 regression while an arm
            # is still running.
            validation_retention = _evaluate_r0(
                graph,
                pools.r0_validation,
                max_samples=0,
                r0_child_triplet_ids=evaluation_child_triplet_ids,
                child_dispatch_cache=evaluation_child_dispatch_cache,
                r0_child_authority=evaluation_child_authority,
                r0_core_graph=r0_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=r0_core_triplet_ids,
                allow_frozen_core=(
                    r0_core_graph is not None and r0_core_gate is not None
                ),
                action_selection_mode=config.r1_action_selection_mode,
            )
            v2_shell_coverage_active = bool(
                r0_child_authority is not None
                and config.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
            )
            validation_retention = _annotate_r0_metric(
                validation_retention,
                metric_name=(
                    "r0_v2_shell_coverage"
                    if v2_shell_coverage_active
                    else "r0_validation_retention"
                ),
                metric_semantics=(
                    "native_v2_shell_available_mate_coverage;"
                    "not_frozen_graph_retention"
                    if v2_shell_coverage_active
                    else "validation_retention_for_current_legacy_routing"
                ),
                source=(
                    "native_v2_authority_graph_emission"
                    if v2_shell_coverage_active
                    else "current_r1_routing"
                ),
                compatibility_key="r0_validation_retention",
            )
            frozen_native_policy_retention = (
                _evaluate_frozen_native_r0_policy(
                    frozen_native_policy_graph,
                    pools.r0_validation,
                    max_samples=0,
                    source=(
                        "authority.base.r0.graph"
                        if r0_child_authority is not None
                        else "isolated_post_r0_graph"
                    ),
                )
            )
            latest_checkpoint = {
                "epoch": epoch_number,
                "validation_conversion_rate": metrics["conversion_rate"],
                "validation_stratum_conversion": metrics["stratum_conversion"],
                "child_handoff_count": counters["child_handoffs"],
                # Keep the historical key for consumers, but make its
                # semantics explicit: in adaptive V2 this compatibility key
                # reports shell coverage, not frozen-graph forgetting.
                "r0_retention_accuracy": validation_retention["accuracy"],
                "r0_validation_retention_accuracy": validation_retention[
                    "accuracy"
                ],
                "r0_validation_retention_metric": validation_retention[
                    "metric_name"
                ],
                "r0_validation_retention_semantics": validation_retention[
                    "metric_semantics"
                ],
                "r0_frozen_native_policy_retention_accuracy": (
                    None
                    if frozen_native_policy_retention is None
                    else frozen_native_policy_retention["accuracy"]
                ),
                "r0_v2_shell_coverage_accuracy": (
                    validation_retention["accuracy"]
                    if v2_shell_coverage_active
                    else None
                ),
            }
            validation_mastery = bool(
                arm.bootstrap_enabled
                and metrics["conversion_rate"] >= config.r1_mastery_threshold
                and validation_retention["accuracy"] >= config.r0_mastery_threshold
            )
            latest_checkpoint["validation_mastery"] = validation_mastery
            # The historical snapshot field is retained for exact resume
            # compatibility, but it now means validation-selected stop.  The
            # regression split is withheld until the one final evaluation.
            joint_mastery = bool(
                validation_mastery
                and config.validation_controls_stage_transitions
            )
            latest_checkpoint["validation_controls_stage_transitions"] = (
                config.validation_controls_stage_transitions
            )
            latest_checkpoint["validation_report_only"] = not bool(
                config.validation_controls_stage_transitions
            )
            latest_checkpoint["joint_mastery"] = joint_mastery
            latest_checkpoint["regression_withheld_from_selection"] = True
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
            if boundary_ecology is not None:
                _verify_boundary_ecology_alignment(
                    r0_child_authority,
                    boundary_ecology,
                    roundtrip=True,
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
                "r0_core_routing": protected_core_identity,
                "epoch_budget": epoch_budget,
                "next_epoch": epoch_number,
                "graph": graph,
                "credit": credit,
                "counters": counters,
                "reply_orbits": reply_orbits,
                "reply_exposure_counts": reply_exposure_counts,
                "reply_exposure_counts_by_reply": reply_exposure_counts_by_reply,
                "child_dispatch_cache": child_dispatch_cache,
                "shuffled_schedule": shuffled_schedule,
                "shuffled_schedule_audit": shuffled_schedule_audit,
                "checkpoints": checkpoints,
                "composition_events": composition_events,
                "composition_consolidation_events": composition_consolidation_events,
                "v2_structural_events": v2_structural_events,
                "reply_policy": effective_reply_policy,
                "reply_policy_events": reply_policy_events,
                "reply_policy_event_digest": reply_policy_event_digest,
                "local_action_events": local_action_events,
                "local_action_positive_credit_options": tuple(
                    sorted(local_action_positive_credit_options)
                ),
                "local_action_event_digest": local_action_event_digest,
                "r0_child_authority_payload": authority_payload,
                "boundary_ecology_manifest": (
                    None
                    if boundary_ecology is None
                    else boundary_ecology.manifest()
                ),
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
        r0_core_graph=r0_core_graph,
        r0_core_gate=r0_core_gate,
        r0_core_triplet_ids=r0_core_triplet_ids,
        action_selection_mode=config.r1_action_selection_mode,
    )
    if defer_regression_evaluation:
        final_regression = None
    else:
        final_regression = _evaluate_r1(
            graph,
            pools.r1_regression,
            strata=pools.r1_regression_strata,
            max_samples=config.max_samples,
            r0_child_triplet_ids=evaluation_child_triplet_ids,
            child_dispatch_cache=evaluation_child_dispatch_cache,
            r0_child_authority=evaluation_child_authority,
            r0_core_graph=r0_core_graph,
            r0_core_gate=r0_core_gate,
            r0_core_triplet_ids=r0_core_triplet_ids,
            action_selection_mode=config.r1_action_selection_mode,
        )
    v2_shell_coverage_active = bool(
        r0_child_authority is not None
        and config.r1_action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
    )
    final_r0_validation_retention = _evaluate_r0(
        graph,
        pools.r0_validation,
        max_samples=config.max_samples,
        r0_child_triplet_ids=evaluation_child_triplet_ids,
        child_dispatch_cache=evaluation_child_dispatch_cache,
        r0_child_authority=evaluation_child_authority,
        r0_core_graph=r0_core_graph,
        r0_core_gate=r0_core_gate,
        r0_core_triplet_ids=r0_core_triplet_ids,
        allow_frozen_core=(r0_core_graph is not None and r0_core_gate is not None),
        action_selection_mode=config.r1_action_selection_mode,
    )
    final_r0_validation_retention = _annotate_r0_metric(
        final_r0_validation_retention,
        metric_name=(
            "r0_v2_shell_coverage"
            if v2_shell_coverage_active
            else "r0_validation_retention"
        ),
        metric_semantics=(
            "native_v2_shell_available_mate_coverage;"
            "not_frozen_graph_retention"
            if v2_shell_coverage_active
            else "validation_retention_for_current_legacy_routing"
        ),
        source=(
            "native_v2_authority_graph_emission"
            if v2_shell_coverage_active
            else "current_r1_routing"
        ),
        compatibility_key="r0_validation_retention",
    )
    final_r0_frozen_native_policy_retention = (
        _evaluate_frozen_native_r0_policy(
            frozen_native_policy_graph,
            pools.r0_validation,
            max_samples=config.max_samples,
            source=(
                "authority.base.r0.graph"
                if r0_child_authority is not None
                else "isolated_post_r0_graph"
            ),
        )
    )
    if defer_regression_evaluation:
        final_r0_regression_retention = None
        final_regression_pass_report_only = None
    else:
        # The arm's final report may measure R0 regression retention once,
        # after its validation-selected training has ended.  It is never used
        # to promote, consolidate, freeze, or stop this arm.
        final_r0_regression_retention = _evaluate_r0(
            graph,
            pools.r0_regression,
            max_samples=config.max_samples,
            r0_child_triplet_ids=evaluation_child_triplet_ids,
            child_dispatch_cache=evaluation_child_dispatch_cache,
            r0_child_authority=evaluation_child_authority,
            r0_core_graph=r0_core_graph,
            r0_core_gate=r0_core_gate,
            r0_core_triplet_ids=r0_core_triplet_ids,
            allow_frozen_core=(
                r0_core_graph is not None and r0_core_gate is not None
            ),
            action_selection_mode=config.r1_action_selection_mode,
        )
        final_r0_regression_retention = _annotate_r0_metric(
            final_r0_regression_retention,
            metric_name=(
                "r0_v2_shell_coverage"
                if v2_shell_coverage_active
                else "r0_regression_retention"
            ),
            metric_semantics=(
                "native_v2_shell_available_mate_coverage;"
                "not_frozen_graph_retention"
                if v2_shell_coverage_active
                else "regression_retention_for_current_legacy_routing"
            ),
            source=(
                "native_v2_authority_graph_emission"
                if v2_shell_coverage_active
                else "current_r1_routing"
            ),
            compatibility_key="r0_regression_retention",
        )
        final_regression_pass_report_only = bool(
            final_regression["conversion_rate"] >= config.r1_mastery_threshold
            and final_r0_regression_retention["accuracy"]
            >= config.r0_mastery_threshold
        )
    current_child_priority = bool(
        evaluation_child_triplet_ids is not None
        or evaluation_child_authority is not None
    )
    current_routing_name = (
        "native_local_first_move_with_certified_successor"
        if config.r1_action_selection_mode
        == R1_ACTION_SELECTION_LOCAL_RECON
        else (
            "child_priority_on"
            if current_child_priority else "child_priority_off"
        )
    )
    current_routing: dict[str, Any] = {
        "validation": final_validation,
        "regression": final_regression,
        "reused_main_evaluation": True,
        "descendant_priority_enabled": bool(
            current_child_priority
            and config.r1_action_selection_mode
            != R1_ACTION_SELECTION_LOCAL_RECON
        ),
        "native_successor_authority_enabled": bool(
            evaluation_child_authority is not None
        ),
        "protected_core_held_constant": bool(
            r0_core_graph is not None and r0_core_gate is not None
        ),
    }
    if defer_regression_evaluation:
        current_routing["regression_withheld_from_routing_ablation"] = True
    routing_ablation: dict[str, Any] = {
        current_routing_name: current_routing,
    }
    if config.r1_action_selection_mode != R1_ACTION_SELECTION_LOCAL_RECON:
        alternate_routing_name = (
            "child_priority_off"
            if current_child_priority else "child_priority_on"
        )
        alternate_ids = (
            None if current_child_priority else r0_child_triplet_ids
        )
        alternate_authority = (
            None if current_child_priority else r0_child_authority
        )
        alternate_cache = (
            child_dispatch_cache if alternate_ids is not None else None
        )
        routing_ablation[alternate_routing_name] = {
            "validation": _evaluate_r1(
                graph,
                pools.r1_validation,
                strata=pools.r1_validation_strata,
                max_samples=0,
                r0_child_triplet_ids=alternate_ids,
                child_dispatch_cache=alternate_cache,
                r0_child_authority=alternate_authority,
                r0_core_graph=r0_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=r0_core_triplet_ids,
                action_selection_mode=config.r1_action_selection_mode,
            ),
            "regression": None,
            "regression_withheld_from_routing_ablation": True,
            "reused_main_evaluation": False,
            "descendant_priority_enabled": not current_child_priority,
            "protected_core_held_constant": bool(
                r0_core_graph is not None and r0_core_gate is not None
            ),
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
            "live_candidate_count": sum(
                not getattr(state, "retired", False)
                for state in r0_child_authority.states.values()
            ),
            "retired_candidate_count": sum(
                getattr(state, "retired", False)
                for state in r0_child_authority.states.values()
            ),
            "retirement_tombstone_count": len(
                getattr(r0_child_authority, "retired_tombstones", {})
            ),
            "live_successor_count": len(
                r0_child_authority.live_successor_ids()
                if callable(
                    getattr(r0_child_authority, "live_successor_ids", None)
                )
                else ()
            ),
            "prospectively_certified_count": sum(
                state.prospectively_certified
                for state in r0_child_authority.states.values()
            ),
            "prospectively_certified_available_count": sum(
                state.prospectively_certified
                and state.hypothesis.polarity
                is AvailabilityState.AVAILABLE
                and not getattr(state, "retired", False)
                for state in r0_child_authority.states.values()
            ),
            "certification_discovery_leak_count": sum(
                bool(
                    set(state.certification_receipt_ids).intersection(
                        state.hypothesis.discovery_exclusion_receipt_ids
                    )
                )
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
    boundary_ecology_audit: dict[str, Any] = {
        "enabled": False,
        "reason": "adaptive_boundary_ecology_disabled",
    }
    adaptive_positive_lineages: dict[str, Any] = (
        _adaptive_positive_lineage_audit(None, None)
    )
    if boundary_ecology is not None:
        _verify_boundary_ecology_alignment(
            r0_child_authority,
            boundary_ecology,
            roundtrip=True,
        )
        ecology_manifest = boundary_ecology.manifest()
        lifecycle_counts = {
            lifecycle.value: sum(
                item.state is lifecycle
                for item in boundary_ecology.sketches.values()
            )
            for lifecycle in SketchLifecycle
        }
        boundary_ecology_audit = {
            "enabled": True,
            "frontier_ordinal": boundary_ecology.frontier_ordinal,
            "observation_count": len(boundary_ecology.observations),
            "lifetime_birth_count": boundary_ecology.lifetime_birth_count,
            "active_candidate_count": boundary_ecology.active_sketch_count,
            "tombstone_count": len(boundary_ecology.tombstones),
            "promotion_count": sum(
                item.retirement_reason == "promoted"
                for item in boundary_ecology.tombstones.values()
            ),
            "positive_only": all(
                item.polarity is True
                for item in boundary_ecology.sketches.values()
            ),
            "refinement_birth_count": sum(
                item.parent_sketch_id is not None
                for item in boundary_ecology.sketches.values()
            ),
            "lifecycle_counts": lifecycle_counts,
            "prune_counts": ecology_manifest["prune_counts"],
            "manifest_digest": boundary_ecology.manifest_digest(),
            "active_candidate_cap": boundary_ecology.config.active_sketch_cap,
            "candidate_width_cap": 3,
        }
        # Keep the detailed candidate-to-authority join in exactly one place;
        # the adjacent ecology section remains summary-only.  The helper is
        # report-only and performs its own fail-closed receipt checks.
        adaptive_positive_lineages = _adaptive_positive_lineage_audit(
            r0_child_authority,
            boundary_ecology,
        )
    v2_authority_audit["adaptive_positive_lineages"] = (
        adaptive_positive_lineages
    )
    result = {
        "training": {
            "episodes": counters["episodes"],
            "epoch_budget": epoch_budget,
            "stopped_epoch": stopped_epoch,
            "joint_mastery": joint_mastery,
            "duration_seconds": round(duration_seconds, 6),
            "resumed_from_snapshot": resumed_from_snapshot,
            "resumed_from_mastered_snapshot": resumed_from_mastered_snapshot,
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
            "r0_core_snapshot_triplet_count": len(r0_core_triplet_ids or ()),
            "r0_core_routing_enabled": bool(
                r0_core_graph is not None and r0_core_gate is not None
            ),
            "r0_core_routing_precedes_v2": bool(
                r0_core_graph is not None and r0_core_gate is not None
            ),
            "r0_core_graph_semantic_state_sha256": (
                None
                if r0_core_graph is None
                else _hash_json(r0_core_graph.canonical_semantic_manifest())
            ),
            "r0_validation_retention_metric": final_r0_validation_retention[
                "metric_name"
            ],
            "r0_validation_retention_semantics": final_r0_validation_retention[
                "metric_semantics"
            ],
            "r0_frozen_native_policy_retention_accuracy": (
                None
                if final_r0_frozen_native_policy_retention is None
                else final_r0_frozen_native_policy_retention["accuracy"]
            ),
            "r0_v2_shell_coverage_accuracy": (
                final_r0_validation_retention["accuracy"]
                if v2_shell_coverage_active
                else None
            ),
            "r0_child_dispatch_cache_entry_count": len(child_dispatch_cache),
            "r0_child_dispatch_cache_hit_count": counters["child_dispatch_cache_hits"],
            "r0_child_dispatch_cache_miss_count": counters["child_dispatch_cache_misses"],
            "r0_child_dispatch_cache_live_mismatch_count": counters["child_dispatch_cache_mismatches"],
            "r0_child_dispatch_cache_certified_hit_count": counters["child_dispatch_cache_certified_hits"],
            "r0_child_cache_validation_mode": config.r0_child_cache_validation_mode,
            "r1_reply_policy_requested": config.r1_reply_policy,
            "r1_reply_policy": effective_reply_policy,
            "r1_reply_policy_active": (
                effective_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
            ),
            "all_reply_envelope_count": counters["reply_envelope_count"],
            "all_reply_envelope_available_count": counters[
                "reply_envelope_available_count"
            ],
            "all_reply_envelope_unknown_count": counters[
                "reply_envelope_unknown_count"
            ],
            "all_reply_envelope_refuted_count": counters[
                "reply_envelope_refuted_count"
            ],
            "all_reply_envelope_positive_count": counters[
                "reply_envelope_positive_count"
            ],
            "all_reply_virtual_query_count": counters[
                "reply_virtual_query_count"
            ],
            "all_reply_terminal_refuted_count": counters[
                "reply_terminal_refuted_count"
            ],
            "all_reply_counterexample_count": counters[
                "reply_counterexample_count"
            ],
            "all_reply_counterexample_real_event_count": counters[
                "reply_counterexample_real_event_count"
            ],
            "all_reply_counterexample_duplicate_virtual_count": counters[
                "reply_counterexample_duplicate_virtual_count"
            ],
            "all_reply_counterexample_mate_count": counters[
                "reply_counterexample_mate_count"
            ],
            "all_reply_counterexample_failure_count": counters[
                "reply_counterexample_failure_count"
            ],
            "all_reply_counterexample_surprise_success_count": counters[
                "reply_counterexample_surprise_success_count"
            ],
            "all_reply_counterexample_false_authority_count": counters[
                "reply_counterexample_false_authority_count"
            ],
            "all_reply_counterexample_handoff_count": counters[
                "reply_counterexample_handoff_count"
            ],
            "reply_exposure_manifest": [
                {
                    "fen": key[0],
                    "white_move": key[1],
                    "black_move": key[2],
                    "reply_id": _r1_reply_id(*key),
                    "exposure_count": int(value),
                }
                for key, value in sorted(reply_exposure_counts_by_reply.items())
            ],
            "reply_policy_event_count": counters["reply_envelope_count"],
            "reply_policy_event_digest": reply_policy_event_digest,
            "reply_policy_recent_events": list(reply_policy_events),
            "reply_policy_manifest": _r1_reply_policy_manifest(
                config,
                effective_policy=effective_reply_policy,
                counters=counters,
                events=reply_policy_events,
                event_digest=reply_policy_event_digest,
                exposure_counts=reply_exposure_counts_by_reply,
            ),
            "v2_real_observation_count": counters.get("v2_real_observations", 0),
            "v2_duplicate_virtual_query_count": counters.get(
                "v2_duplicate_virtual_queries", 0
            ),
            "v2_structural_transition_count": counters.get(
                "v2_structural_transitions", 0
            ),
            "v2_availability_used_for_bootstrap": bool(arm.bootstrap_enabled),
            "v2_same_event_outcome_used_for_bootstrap": False,
            "boundary_ecology": boundary_ecology_audit,
            "observed_terminal_failure_count": counters["failures"],
            "unique_first_move_reply_exposures": len(reply_orbits),
            "distinct_first_move_actions_exposed": (
                len({
                    (key[0], key[1])
                    for key in reply_exposure_counts_by_reply
                })
                if effective_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else len(reply_exposure_counts)
            ),
            "distinct_exact_reply_exposures": len(
                reply_exposure_counts_by_reply
            ),
            "r1_action_order": config.r1_action_order,
            "r1_action_selection_mode": config.r1_action_selection_mode,
            "r1_action_order_key": (
                "not_used_graph_local_anonymous_competition"
                if config.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else (
                    "lexicographic_uci_ids"
                    if config.r1_action_order
                    == R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
                    else "generic_seed_plus_opaque_position_identity"
                )
            ),
            "local_action_event_count": (
                counters["episodes"]
                if config.r1_action_selection_mode
                == R1_ACTION_SELECTION_LOCAL_RECON
                else 0
            ),
            "local_action_event_digest": local_action_event_digest,
            "local_action_recent_events": list(local_action_events),
            "local_action_first_contact_selection_count": counters[
                "local_action_first_contact_selections"
            ],
            "local_action_post_contact_selection_count": counters[
                "local_action_post_contact_selections"
            ],
            "local_action_exact_q_selection_count": counters[
                "local_action_exact_q_selections"
            ],
            "local_action_positive_credit_revisit_count": counters[
                "local_action_positive_credit_revisits"
            ],
            "local_action_positive_credit_option_count": len(
                local_action_positive_credit_options
            ),
            "local_action_lifetime_evidence_is_report_only": True,
            "local_candidate_counter_scope": (
                "lifetime_graph_including_r0_and_read_only_evaluation"
            ),
            "local_candidate_pairs_before_cap": int(
                graph.scheduler_stats.get(
                    "shared_atom_candidate_pairs_before_cap", 0
                )
            ),
            "local_candidate_pairs_after_cap": int(
                graph.scheduler_stats.get(
                    "shared_atom_candidate_pairs_after_cap", 0
                )
            ),
            "local_candidate_cap_bound": bool(
                graph.scheduler_stats.get(
                    "shared_atom_candidate_pairs_before_cap", 0
                )
                > graph.scheduler_stats.get(
                    "shared_atom_candidate_pairs_after_cap", 0
                )
            ),
            "reply_schedule": (
                "worst_authority_state_then_confidence_then_selected_exposure"
                if effective_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else "per_position_action_round_robin"
            ),
            "virtual_reply_probe_schedule": (
                "exhaustive_all_legal_replies"
                if effective_reply_policy
                == R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE
                else "not_applicable"
            ),
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
        "regression_withheld_until_final": True,
        "regression_pass_report_only": final_regression_pass_report_only,
        "routing_ablation": routing_ablation,
        # Compatibility key: historically this was the only retention
        # result.  Its final-arm meaning remains regression retention; all
        # checkpoint and maturity uses the explicit validation field below.
        "r0_retention": final_r0_regression_retention,
        "r0_validation_retention": final_r0_validation_retention,
        "r0_frozen_native_policy_retention": (
            final_r0_frozen_native_policy_retention
        ),
        "r0_v2_shell_coverage": (
            final_r0_validation_retention
            if v2_shell_coverage_active
            else None
        ),
        "r0_regression_retention": final_r0_regression_retention,
        "graph": graph.learned_state_audit(),
        "credit": credit.snapshot(),
        "v2_child_authority": v2_authority_audit,
    }
    if defer_regression_evaluation:
        # This private handoff is consumed by the top-level runner after the
        # last arm finishes.  It is removed before the result is serialized.
        result["_terminal_regression_context"] = {
            "graph": graph,
            "r0_child_triplet_ids": evaluation_child_triplet_ids,
            "child_dispatch_cache": evaluation_child_dispatch_cache,
            "r0_child_authority": evaluation_child_authority,
            # V2 regression routing resolves the cloned authority's immutable
            # source on demand; do not retain another graph object in the
            # deferred context.  Legacy callers still carry their report copy.
            "r0_core_graph": (
                None
                if evaluation_child_authority is not None
                else r0_core_graph
            ),
            "r0_core_gate": r0_core_gate,
            "r0_core_triplet_ids": (
                None
                if evaluation_child_authority is not None
                else r0_core_triplet_ids
            ),
            "current_routing_name": current_routing_name,
        }
    return result

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
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
    action_selection_mode: str = R1_ACTION_SELECTION_SCHEDULED,
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
            r0_core_graph=r0_core_graph,
            r0_core_gate=r0_core_gate,
            r0_core_triplet_ids=r0_core_triplet_ids,
            action_selection_mode=action_selection_mode,
        )
        graph.set_composite_enabled(composite_id, enabled=False)
        disabled = _evaluate_r1(
            graph,
            pools.r1_train,
            strata=pools.r1_train_strata,
            max_samples=len(pools.r1_train),
            r0_child_triplet_ids=r0_child_triplet_ids,
            child_dispatch_cache=child_dispatch_cache,
            r0_core_graph=r0_core_graph,
            r0_core_gate=r0_core_gate,
            r0_core_triplet_ids=r0_core_triplet_ids,
            action_selection_mode=action_selection_mode,
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
    frozen_core_graph: NativeReConKRKGraph | None = None,
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
    response_graph = (
        frozen_core_graph.frame_runtime_copy()
        if frozen_core_graph is not None
        else graph
    )
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
            response_graph.confirm_candidate(
                board,
                triplet_id=experience.triplet_id,
                move_uci=experience.move_uci,
            )
            if experience is not None
            else response_graph.audit_choice(board)
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
        "cache_contains_memoized_move_provider": True,
        "cache_use_is_controlled_by_r0_replay_per_r1_epoch": True,
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
    validation_retention = arm["r0_validation_retention"]
    frozen_retention = arm.get("r0_frozen_native_policy_retention")
    shell_coverage = arm.get("r0_v2_shell_coverage")
    return {
        "training_episodes": arm["training"]["episodes"],
        "stopped_epoch": arm["training"]["stopped_epoch"],
        "joint_mastery": arm["training"]["joint_mastery"],
        "child_handoff_count": arm["training"]["child_handoff_count"],
        "r0_replay_episode_count": arm["training"]["r0_replay_episode_count"],
        "validation_conversion_rate": arm["validation"]["conversion_rate"],
        "r0_retention_accuracy": validation_retention["accuracy"],
        "r0_validation_retention_accuracy": validation_retention["accuracy"],
        "r0_validation_retention_metric": validation_retention.get(
            "metric_name", "r0_validation_retention"
        ),
        "r0_validation_retention_semantics": validation_retention.get(
            "metric_semantics", "legacy_unannotated_retention"
        ),
        "r0_frozen_native_policy_retention_accuracy": (
            None
            if not isinstance(frozen_retention, Mapping)
            else frozen_retention.get("accuracy")
        ),
        "r0_v2_shell_coverage_accuracy": (
            None
            if not isinstance(shell_coverage, Mapping)
            else shell_coverage.get("accuracy")
        ),
        "regression_withheld_until_final": True,
    }


def _opaque_r1_position_identity(fen: str, position_index: int) -> str:
    """Derive an opaque, stable identity for one R1 pool position.

    The identity is used only to permute otherwise legal actuator IDs.  It is
    never exposed as a learner feature or used to select a move semantically.
    Hashing the pool position and its canonical board serialization keeps the
    permutation stable across epochs while preventing UCI-order clustering.
    """

    return hashlib.blake2b(
        f"r1-position|{int(position_index)}|{str(fen)}".encode("utf-8"),
        digest_size=16,
    ).hexdigest()


def _stable_hash_action_permutation(
    actuator_ids: Sequence[str],
    *,
    generic_seed: int,
    position_identity: str,
) -> tuple[str, ...]:
    """Return a deterministic permutation of opaque legal actuator IDs."""

    identifiers = tuple(str(item) for item in actuator_ids)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("actuator IDs must be unique")
    return tuple(
        item
        for _key, item in sorted(
            (
                hashlib.blake2b(
                    (
                        f"r1-action-order|{int(generic_seed)}|"
                        f"{str(position_identity)}|{item}"
                    ).encode("utf-8"),
                    digest_size=16,
                ).digest(),
                item,
            )
            for item in identifiers
        )
    )


def _r1_legal_action_order(
    board: chess.Board,
    *,
    action_order: str = R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
    generic_seed: int = 0,
    position_identity: str = "",
) -> tuple[chess.Move, ...]:
    """Order legal R1 actuators without changing the legacy R0 policy."""

    legal = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))
    normalized = str(action_order).strip().lower()
    if normalized in {
        "legacy",
        "lexicographic",
        R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
    }:
        return legal
    if normalized not in {
        "stable_hash",
        "hash_permutation",
        R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
    }:
        raise ValueError(f"unsupported R1 action order: {action_order}")
    identifiers = _stable_hash_action_permutation(
        tuple(item.uci() for item in legal),
        generic_seed=int(generic_seed),
        position_identity=str(position_identity),
    )
    return tuple(chess.Move.from_uci(item) for item in identifiers)


# Concise aliases are useful to small development tests while the longer
# names make the configuration and artifact semantics self-documenting.
_stable_hash_permutation = _stable_hash_action_permutation
_r1_action_order = _r1_legal_action_order


def _scheduled_confirmed_action(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    *,
    schedule_index: int,
    stage_diagnostic: str,
    action_order: str = R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
    generic_seed: int = 0,
    position_identity: str = "",
) -> tuple[chess.Move, str, bool, float]:
    legal = _r1_legal_action_order(
        board,
        action_order=action_order,
        generic_seed=generic_seed,
        position_identity=position_identity,
    )
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


def _select_r1_training_action(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    *,
    epoch: int,
    position_index: int,
    fen: str,
    config: NativeIntrinsicCurriculumConfig,
) -> tuple[chess.Move, str, bool, float, dict[str, Any] | None]:
    """Select one R1 action without letting the harness rank local choices.

    The legacy mode is retained for exact historical replay.  In native-local
    mode the host supplies only the legal environment; the graph creates the
    candidate activations and ``AnonymousChoiceGenome`` emits one actuator.
    The returned manifest is diagnostic and cannot affect the decision.
    """

    if config.r1_action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON:
        decision = graph.choose_local_training_action(
            board,
            stage_diagnostic="R1_mate_in_2",
        )
        move = chess.Move.from_uci(str(decision.move_uci))
        if move not in board.legal_moves:
            raise RuntimeError("native local selector emitted an illegal R1 move")
        if not bool(decision.confirmed):
            raise RuntimeError(
                "native local selector could not formally confirm its emitted "
                "exact R1 branch"
            )
        return (
            move,
            str(decision.triplet_id),
            bool(decision.confirmed),
            float(decision.prediction),
            dict(decision.to_manifest()),
        )

    if config.r1_action_selection_mode != R1_ACTION_SELECTION_SCHEDULED:
        raise ValueError(
            "unsupported R1 action selection mode: "
            f"{config.r1_action_selection_mode}"
        )
    move, triplet_id, confirmed, prediction = _scheduled_confirmed_action(
        graph,
        board,
        schedule_index=epoch + position_index,
        stage_diagnostic="R1_mate_in_2",
        action_order=config.r1_action_order,
        generic_seed=config.seed,
        position_identity=_opaque_r1_position_identity(fen, position_index),
    )
    return move, triplet_id, confirmed, prediction, None


def _supported_local_policy_action(
    graph: NativeReConKRKGraph,
    board: chess.Board,
) -> chess.Move | None:
    """Return a learned local action, or abstain without native support.

    Anonymous emission confirms a legal actuator affordance.  Scientific
    evaluation additionally requires that a persistent, formally confirmed
    graph source supplied the winning pattern's value.  This prevents an
    empty graph's deterministic zero-score tie break from being counted as
    learned competence.
    """

    decision = graph.choose_local_policy_action(board)
    if decision is None:
        return None
    if not bool(decision.policy_supported):
        return None
    move = decision.move
    if move not in board.legal_moves:
        raise RuntimeError("supported native local policy emitted an illegal move")
    return move


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
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
    allow_frozen_core: bool = False,
    allow_legacy_child_priority: bool | None = None,
) -> chess.Move | None:
    """Route through the local frozen core, V2, then the grown graph.

    A protected post-R0 shell is queried for every policy board supplied to
    this function.  Its learned local gate, rather than a caller's stage or
    position label, decides whether it has jurisdiction.  An AVAILABLE core
    response therefore preempts a descendant; an abstention lets a grounded
    V2 descendant and finally the plastic graph compete normally.  The legacy
    ``virtual_frame_verified`` child path is disabled whenever a protected
    core is present: that path evaluates the mutable graph and could recreate
    a mate solely from shared topology after the local core has abstained.
    """

    core_routing_requested = bool(
        r0_core_graph is not None
        or r0_core_gate is not None
        or r0_core_triplet_ids is not None
    )
    if r0_child_authority is not None and core_routing_requested:
        authority_r0 = getattr(
            getattr(r0_child_authority, "base", None), "r0", None
        )
        authority_graph = getattr(authority_r0, "graph", None)
        authority_triplets = getattr(authority_r0, "frozen_triplet_ids", None)
        if authority_graph is not None and authority_triplets is not None:
            if r0_core_graph is not None and _hash_json(
                r0_core_graph.canonical_semantic_manifest()
            ) != _hash_json(authority_graph.canonical_semantic_manifest()):
                raise RuntimeError(
                    "explicit protected core differs from V2 authority R0 source"
                )
            if (
                r0_core_triplet_ids is not None
                and frozenset(r0_core_triplet_ids)
                != frozenset(authority_triplets)
            ):
                raise RuntimeError(
                    "explicit protected core IDs differ from V2 authority R0 source"
                )
            r0_core_graph = authority_graph
            r0_core_triplet_ids = frozenset(authority_triplets)

    protected_core_supplied = bool(
        r0_core_graph is not None or r0_core_gate is not None
        or r0_core_triplet_ids is not None
    )
    if protected_core_supplied and (
        r0_core_graph is None or r0_core_gate is None
    ):
        raise ValueError(
            "protected core routing requires a graph and local gate"
        )
    # ``allow_frozen_core`` remains a compatibility guard for older direct
    # callers, but the presence of the protected inputs is itself sufficient.
    # This prevents a first-vs-successor stage flag from changing routing.
    core_enabled = bool(
        r0_core_graph is not None and r0_core_gate is not None
    )
    if allow_frozen_core and not core_enabled:
        raise ValueError(
            "allow_frozen_core requires a protected graph and local gate"
        )

    if core_enabled:
        core_triplet_ids = (
            frozenset(r0_core_graph.triplet_ids)
            if r0_core_triplet_ids is None
            else frozenset(r0_core_triplet_ids)
        )
        if not core_triplet_ids.issubset(r0_core_graph.triplet_ids):
            raise ValueError("protected R0 core triplet ids are not in its graph")
        available, response = _protected_core_r0_available(
            r0_core_graph,
            r0_core_gate,
            board,
            allowed_triplets=core_triplet_ids,
            authority=r0_child_authority,
        )
        selected_uci = response.get("selected_move")
        if available and selected_uci is not None:
            move = chess.Move.from_uci(str(selected_uci))
            if move in board.legal_moves:
                return move

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
    # Never use the old outcome-observing grown-graph shortcut as a fallback
    # once an immutable core was supplied.  Core abstention must mean genuine
    # abstention, not a second chance for the mutable graph to claim the old
    # child triplet.  With no protected core, preserve legacy semantics.
    legacy_child_allowed = (
        False
        if core_enabled
        else (
            not allow_frozen_core
            if allow_legacy_child_priority is None
            else bool(allow_legacy_child_priority)
        )
    )
    if r0_child_triplet_ids and legacy_child_allowed:
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
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
    allow_frozen_core: bool = False,
    allow_legacy_child_priority: bool | None = None,
    action_selection_mode: str = R1_ACTION_SELECTION_SCHEDULED,
) -> dict[str, Any]:
    local_source_ablation = bool(
        action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
        and masked_triplets
    )
    if (
        r0_child_authority is not None
        and r0_core_graph is None
        and r0_core_gate is not None
    ):
        authority_r0 = getattr(
            getattr(r0_child_authority, "base", None), "r0", None
        )
        authority_graph = getattr(authority_r0, "graph", None)
        authority_triplets = getattr(authority_r0, "frozen_triplet_ids", None)
        if authority_graph is not None and authority_triplets is not None:
            r0_core_graph = authority_graph
            r0_core_triplet_ids = frozenset(authority_triplets)
    rows: list[dict[str, Any]] = []
    correct = illegal = null = stalemate = rook_loss = 0
    for fen in fens:
        board = chess.Board(fen)
        if local_source_ablation:
            # A local-policy ablation means that every learned native source
            # is unavailable. Abstain explicitly; falling through to the
            # legacy graph chooser would introduce a second hidden picker and
            # make the enabled/disabled intervention incomparable.
            move = None
        elif (
            action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
            and r0_child_authority is not None
            and not masked_triplets
        ):
            available, response = _v2_r0_available(
                r0_child_authority,
                board,
                frame_id=(
                    "native-intrinsic-v2-r0-evaluation:"
                    + hashlib.sha256(board.fen().encode("utf-8")).hexdigest()
                ),
            )
            selected_uci = response.get("selected_move") if available else None
            candidate = (
                None
                if selected_uci is None
                else chess.Move.from_uci(str(selected_uci))
            )
            move = (
                candidate
                if candidate is not None and candidate in board.legal_moves
                else None
            )
        elif (
            action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
            and not masked_triplets
        ):
            move = _supported_local_policy_action(graph, board)
        else:
            move = (
                _choose_with_child_priority(
                    graph,
                    board,
                    r0_child_triplet_ids=r0_child_triplet_ids,
                    child_dispatch_cache=child_dispatch_cache,
                    r0_child_authority=r0_child_authority,
                    r0_core_graph=r0_core_graph,
                    r0_core_gate=r0_core_gate,
                    r0_core_triplet_ids=r0_core_triplet_ids,
                    allow_frozen_core=allow_frozen_core,
                    allow_legacy_child_priority=allow_legacy_child_priority,
                )
                if (
                    r0_child_triplet_ids
                    or r0_child_authority is not None
                    or allow_frozen_core
                    or (
                        r0_core_graph is not None
                        and r0_core_gate is not None
                    )
                )
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
        "action_selection_mode": action_selection_mode,
        "effective_action_selection_mode": (
            "native_local_all_sources_masked_abstention"
            if local_source_ablation
            else action_selection_mode
        ),
        "native_authority_fail_closed": bool(
            action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
            and r0_child_authority is not None
        ),
        "samples": rows,
    }


def _copy_frozen_native_r0_graph(
    graph: NativeReConKRKGraph,
    *,
    r0_child_authority: Any | None = None,
    r0_core_graph: NativeReConKRKGraph | None = None,
) -> NativeReConKRKGraph | None:
    """Return an isolated copy of the immutable native R0 policy source.

    Adaptive V2 evaluation has two distinct jurisdictions: the frozen R0
    graph and the prospective V2 shell.  The authority owns the former, so
    resolve that source explicitly instead of reusing a shell query as a
    retention measurement.  A legacy core copy remains the source for
    compatibility arms; absent either, the arm's graph is the pre-R1 source.
    """

    if r0_child_authority is not None:
        authority_r0 = getattr(
            getattr(r0_child_authority, "base", None), "r0", None
        )
        authority_graph = getattr(authority_r0, "graph", None)
        if authority_graph is None:
            return None
        return copy.deepcopy(authority_graph)
    source = r0_core_graph if r0_core_graph is not None else graph
    return copy.deepcopy(source)


def _annotate_r0_metric(
    metrics: Mapping[str, Any] | None,
    *,
    metric_name: str,
    metric_semantics: str,
    source: str,
    compatibility_key: str | None = None,
) -> dict[str, Any] | None:
    """Attach an explicit jurisdiction to a compatibility R0 metric."""

    if metrics is None:
        return None
    annotated = dict(metrics)
    annotated.update({
        "metric_name": metric_name,
        "metric_semantics": metric_semantics,
        "metric_source": source,
    })
    if compatibility_key is not None:
        annotated["compatibility_key"] = compatibility_key
    return annotated


def _evaluate_frozen_native_r0_policy(
    frozen_graph: NativeReConKRKGraph | None,
    fens: Sequence[str],
    *,
    max_samples: int,
    source: str = "isolated_frozen_r0_graph",
) -> dict[str, Any] | None:
    """Measure retention of the frozen graph, excluding the V2 shell."""

    if frozen_graph is None:
        return None
    metrics = _evaluate_r0(
        frozen_graph,
        fens,
        max_samples=max_samples,
        action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
    )
    return _annotate_r0_metric(
        metrics,
        metric_name="r0_frozen_native_policy_retention",
        metric_semantics=(
            "frozen_native_r0_graph_policy_retention;"
            "v2_shell_excluded"
        ),
        source=source,
    )


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
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
    action_selection_mode: str = R1_ACTION_SELECTION_SCHEDULED,
) -> dict[str, Any]:
    if (
        r0_child_authority is not None
        and r0_core_graph is None
        and r0_core_gate is not None
    ):
        authority_r0 = getattr(
            getattr(r0_child_authority, "base", None), "r0", None
        )
        authority_graph = getattr(authority_r0, "graph", None)
        authority_triplets = getattr(authority_r0, "frozen_triplet_ids", None)
        if authority_graph is not None and authority_triplets is not None:
            r0_core_graph = authority_graph
            r0_core_triplet_ids = frozenset(authority_triplets)
    rows: list[dict[str, Any]] = []
    converted = null = illegal = reply_total = reply_mated = 0
    if strata is not None and len(strata) != len(fens):
        raise ValueError("R1 evaluation FEN and stratum sequences must align")
    stratum_conversion: dict[str, dict[str, int | float]] = {}
    for position_index, fen in enumerate(fens):
        stratum = "unstratified" if strata is None else str(strata[position_index])
        board = chess.Board(fen)
        first = (
            _supported_local_policy_action(graph, board)
            if action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON
            else _choose_with_child_priority(
                graph,
                board,
                r0_child_triplet_ids=r0_child_triplet_ids,
                child_dispatch_cache=child_dispatch_cache,
                r0_child_authority=r0_child_authority,
                r0_core_graph=r0_core_graph,
                r0_core_gate=r0_core_gate,
                r0_core_triplet_ids=r0_core_triplet_ids,
                allow_frozen_core=(
                    r0_core_graph is not None and r0_core_gate is not None
                ),
                allow_legacy_child_priority=(
                    r0_core_graph is None or r0_core_gate is None
                ),
            )
        )
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
                if action_selection_mode == R1_ACTION_SELECTION_LOCAL_RECON:
                    if r0_child_authority is None:
                        second = _supported_local_policy_action(
                            graph,
                            before_second,
                        )
                    else:
                        available, response = _v2_r0_available(
                            r0_child_authority,
                            before_second,
                            frame_id=(
                                "native-intrinsic-v2-r1-evaluation-successor:"
                                + hashlib.sha256(
                                    before_second.fen().encode("utf-8")
                                ).hexdigest()
                            ),
                        )
                        selected_uci = (
                            response.get("selected_move") if available else None
                        )
                        candidate = (
                            None
                            if selected_uci is None
                            else chess.Move.from_uci(str(selected_uci))
                        )
                        second = (
                            candidate
                            if candidate is not None
                            and candidate in before_second.legal_moves
                            else None
                        )
                else:
                    second = _choose_with_child_priority(
                        graph,
                        before_second,
                        r0_child_triplet_ids=r0_child_triplet_ids,
                        child_dispatch_cache=child_dispatch_cache,
                        r0_child_authority=r0_child_authority,
                        r0_core_graph=r0_core_graph,
                        r0_core_gate=r0_core_gate,
                        r0_core_triplet_ids=r0_core_triplet_ids,
                        allow_frozen_core=(
                            r0_core_graph is not None and r0_core_gate is not None
                        ),
                        allow_legacy_child_priority=(
                            r0_core_graph is None or r0_core_gate is None
                        ),
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
        "reply_mate_rate": 0.0 if reply_total == 0 else reply_mated / reply_total,
        "reply_evaluation_count": reply_total,
        "null_selection_count": null,
        "illegal_move_count": illegal,
        "reply_evaluation_mode": (
            "early_exit_on_failure" if stop_after_first_failure else "exhaustive"
        ),
        "mature_child_priority_enabled": bool(
            action_selection_mode != R1_ACTION_SELECTION_LOCAL_RECON
            and (r0_child_triplet_ids or r0_child_authority is not None)
        ),
        "certified_successor_authority_enabled": bool(
            r0_child_authority is not None
        ),
        "action_selection_mode": action_selection_mode,
        "adaptive_host_priority_cascade_used": bool(
            action_selection_mode != R1_ACTION_SELECTION_LOCAL_RECON
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
    regression_positive: Sequence[str] = (),
    regression_negative: Sequence[str] = (),
) -> tuple[OutcomeCalibratedPrototypeGate, dict[str, Any]]:
    # The regression arguments remain in the signature for compatibility with
    # older callers and snapshot tooling.  They are intentionally not read:
    # gate selection and maturity are train/validation-only operations.
    del regression_positive, regression_negative
    train = [_gate_example(graph, fen) for fen in (*train_positive, *train_negative)]
    validation = [
        _gate_example(graph, fen)
        for fen in (*validation_positive, *validation_negative)
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
    selection = {
        "selection_split": "gate_validation",
        "confirmation_split": None,
        "candidate_count": len(candidate_rows),
        "candidates": candidate_rows,
        "selected_neighbors": selected.neighbors,
        "selected_threshold": selected.threshold,
        "selected_validation_metrics": dict(selected.validation_metrics),
        "regression_metrics": None,
        "regression_withheld_until_final": True,
        "joint_gate_certification_pass": selected.mature,
    }
    return selected, selection


def _evaluate_r0_gate_regression(
    graph: NativeReConKRKGraph,
    gate: OutcomeCalibratedPrototypeGate,
    *,
    positive_fens: Sequence[str],
    negative_fens: Sequence[str],
) -> dict[str, Any]:
    """Evaluate the selected gate on regression only for the final report.

    This helper deliberately has no side effects on gate maturity.  Calling
    it at any earlier point would turn a report split into a selection signal,
    so the curriculum invokes it exactly once after all stage decisions.
    """

    examples = [
        _gate_example(graph, fen)
        for fen in (*positive_fens, *negative_fens)
    ]
    metrics = gate.evaluate(examples)
    return {
        **metrics,
        "positive_count": len(positive_fens),
        "negative_count": len(negative_fens),
        "split": "gate_regression",
        "selection_influenced": False,
    }


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
    # NativeProspectiveAuthorityV2.open_virtual() owns the bounded pre/post
    # mutation guard.  Re-hashing its complete lifetime continuation here once
    # per legal reply would turn all-reply evaluation back into a superlinear
    # history scan.  Frame-session close and explicit structural/checkpoint
    # boundaries retain the complete source and replay audits.
    actuation = query.actuation
    selected_move = None if actuation is None else str(actuation.move_uci)
    selected_triplet = (
        None
        if actuation is None
        else str(
            getattr(
                actuation,
                "selected_triplet_id",
                actuation.option_identity,
            )
        )
    )
    r0_graph = getattr(
        getattr(getattr(authority, "base", None), "r0", None),
        "graph",
        None,
    )
    exact_action_pattern_id = (
        None
        if selected_move is None or r0_graph is None
        else _triplet_id(
            *_triplet_keys(
                board,
                chess.Move.from_uci(selected_move),
                key_mode=r0_graph.config.key_mode,
            )
        )
    )
    raw_grounded = getattr(query.response, "grounded", None)
    grounded = raw_grounded if type(raw_grounded) is bool else False
    authority_grounded, authority_grounding = _v2_grounding_audit(authority)
    base_provenance = provenance.get("base_availability_provenance")
    local_provider = (
        base_provenance.get("local_provider")
        if isinstance(base_provenance, Mapping)
        else None
    )
    if not isinstance(local_provider, Mapping):
        local_provider = None
    native_provider = provenance.get("native_provider")
    if not isinstance(native_provider, Mapping):
        native_provider = None
    provider = local_provider if local_provider is not None else native_provider
    provider_kind = (
        None if provider is None else str(provider.get("provider_kind", ""))
    )
    response_child_id = getattr(query.response, "child_id", None)
    provider_valid = bool(
        provider is not None
        and _r1_reply_authority_from_provider(
            "provider-validation",
            provider,
            exposure_count=0,
        ).grounded
        and isinstance(response_child_id, str)
        and response_child_id
        and response_child_id == str(provider.get("cell_id"))
    )
    local_direct_mode = bool(
        isinstance(base_provenance, Mapping)
        and base_provenance.get("local_direct_outcome_mode") is True
    )
    available = bool(
        query.response.available
        and grounded
        and (
            provider_valid
            if local_direct_mode
            else (provider_valid or authority_grounded)
        )
    )
    response = {
        "selected_move": selected_move,
        "selected_triplet": selected_triplet,
        "selected_option_identity": (
            None if actuation is None else str(actuation.option_identity)
        ),
        # VIRTUAL availability is a learned capability claim, never an
        # observed world outcome.  Only the REAL path may populate the latter.
        "observed_immediate_mate": None,
        "outcome_observed": False,
        "available_capability": available,
        "exact_action_pattern_id": exact_action_pattern_id,
        "availability_source": "v2_prospective_graph_emission",
        "availability_provenance": provenance,
        "classification": opened["classification"].to_manifest(),
        "grounded": raw_grounded,
        "grounding_source": getattr(query.response, "grounding_source", None),
        "authority_grounding": authority_grounding,
        "local_direct_outcome_mode": local_direct_mode,
        "provider_available": provider_valid,
        "provider_kind": provider_kind if provider_valid else None,
        "provider": None if not provider_valid else dict(provider),
        "local_provider_available": local_provider is not None,
        "local_provider": (
            None if local_provider is None else dict(local_provider)
        ),
        "provider_id": (
            None
            if not provider_valid
            else str(provider["cell_id"])
        ),
        "provider_value": (
            0.0
            if not provider_valid
            else float(provider["expected_value"])
        ),
        "provider_confidence": (
            0.0
            if not provider_valid
            else float(provider["confidence"])
        ),
        "virtual_frame_terminal_grounding_granted": False,
    }
    return available, response


def _native_v2_runtime_integrity_ready(
    audit: Mapping[str, Any] | None,
) -> bool:
    """Use only an exact outcome-blind integrity result for R1 entry."""

    return bool(
        isinstance(audit, Mapping)
        and audit.get("runtime_integrity_pass") is True
    )


def _native_v2_authority_ready_for_r1(
    *,
    availability_mode: str,
    authority_present: bool,
    boundary_ecology_enabled: bool,
    admission_audit: Mapping[str, Any] | None,
) -> bool:
    """Admit native R1 without turning held-out coverage into authority."""

    return bool(
        availability_mode == V2_PROSPECTIVE_AVAILABILITY
        and authority_present
        and (
            not boundary_ecology_enabled
            or _native_v2_runtime_integrity_ready(admission_audit)
        )
    )


def _native_v2_r0_admission_audit(
    authority: Any,
    *,
    positive_fens: Sequence[str],
    negative_fens: Sequence[str],
    max_samples: int,
) -> dict[str, Any]:
    """Report native R0 jurisdiction and verify read-only runtime integrity.

    This is a report-only scientific audit, not a runtime provider or global
    competence gate.  It performs read-only VIRTUAL queries against the
    prospectively closed authority and observes the selected action in a
    copied validation board.  Coverage and specificity never decide whether
    R1 experience exists. Only outcome-blind integrity (immutability and the
    legality of any AVAILABLE graph actuation) can fail stage entry. An empty
    authority is expected to abstain everywhere initially. No validation
    outcome is consumed by the authority, used to alter a cell, or exposed as
    a learner feature.
    """

    continuation_before = str(authority.continuation_digest())
    r0 = getattr(getattr(authority, "base", None), "r0", None)
    if r0 is None or not callable(getattr(r0, "inference_guard_identity", None)):
        raise TypeError("native V2 admission requires an immutable R0 organism")
    source_before = str(r0.inference_guard_identity())
    frame_session_factory = getattr(authority, "frame_session", None)
    frame_session = (
        frame_session_factory() if callable(frame_session_factory) else None
    )
    positive_authorized = positive_mates = negative_available = 0
    available_responses = available_invalid_actuations = 0
    illegal = null = 0
    samples: list[dict[str, Any]] = []
    try:
        for expected_positive, fens in (
            (True, positive_fens),
            (False, negative_fens),
        ):
            for index, fen in enumerate(fens):
                board = chess.Board(fen)
                available, response = _v2_r0_available(
                    authority,
                    board,
                    frame_id=(
                        "native-r0-admission:"
                        f"{'positive' if expected_positive else 'negative'}:"
                        f"{index}"
                    ),
                    frame_session=frame_session,
                )
                selected_uci = response.get("selected_move")
                move: chess.Move | None = None
                if selected_uci is not None:
                    try:
                        move = chess.Move.from_uci(str(selected_uci))
                    except ValueError:
                        move = None
                legal = bool(move is not None and move in board.legal_moves)
                observed_mate = bool(
                    legal
                    and move is not None
                    and _execute_white_and_observe(board, move) == "mate"
                )
                null += int(selected_uci is None)
                illegal += int(selected_uci is not None and not legal)
                available_responses += int(available)
                available_invalid_actuations += int(available and not legal)
                if expected_positive:
                    positive_authorized += int(available and legal)
                    positive_mates += int(available and legal and observed_mate)
                else:
                    negative_available += int(available)
                if len(samples) < max(0, int(max_samples)):
                    samples.append({
                        "split": (
                            "r0_validation_positive"
                            if expected_positive
                            else "r0_validation_decoy"
                        ),
                        "selected_move": selected_uci,
                        "available": bool(available),
                        "legal": legal,
                        "observed_mate": observed_mate,
                        "classification": response.get("classification"),
                    })
    finally:
        if frame_session is not None:
            frame_session.close()

    continuation_after = str(authority.continuation_digest())
    source_after = str(r0.inference_guard_identity())
    positive_count = len(positive_fens)
    negative_count = len(negative_fens)
    immutable = bool(
        continuation_before == continuation_after
        and source_before == source_after
    )
    # Runtime entry depends only on integrity, never on held-out chess
    # outcomes or global coverage.  UNKNOWN is a safe local abstention: it
    # cannot bootstrap a successor, but it must not prevent unrelated R1
    # environmental experience.  The stricter coverage/specificity result
    # below remains report-only.
    runtime_integrity_pass = bool(
        immutable
        and illegal == 0
        and available_invalid_actuations == 0
    )
    passed = bool(
        positive_count > 0
        and positive_authorized == positive_count
        and positive_mates == positive_count
        and negative_available == 0
        and illegal == 0
        and immutable
    )
    return {
        "schema_version": "native_v2_r0_admission.v2",
        "pass": passed,
        "scientific_coverage_specificity_pass": passed,
        "runtime_integrity_pass": runtime_integrity_pass,
        "coverage_specificity_controls_r1_stage_entry": False,
        "runtime_integrity_controls_r1_stage_entry": True,
        "runtime_integrity_checks_all_emitted_actuations": True,
        "positive_count": positive_count,
        "positive_authorized_count": positive_authorized,
        "positive_authorized_mate_count": positive_mates,
        "negative_count": negative_count,
        "negative_available_count": negative_available,
        "available_response_count": available_responses,
        "available_invalid_actuation_count": available_invalid_actuations,
        "illegal_selection_count": illegal,
        "null_selection_count": null,
        "virtual_queries_only": True,
        "validation_outcomes_consumed_by_learner": False,
        "continuation_immutable": continuation_before == continuation_after,
        "frozen_r0_immutable": source_before == source_after,
        "continuation_digest": continuation_after,
        "frozen_r0_inference_guard": source_after,
        "samples": samples,
    }


def _advance_v2_structural_frontier(
    authority: Any,
    *,
    promotions: Sequence[BoundaryPromotionRequest] = (),
) -> dict[str, Any] | None:
    mode = StructuralMode(
        getattr(authority, "structural_mode", StructuralMode.SCHEDULED)
    )
    if mode is StructuralMode.EVENT_DRIVEN:
        pending_reader = getattr(authority, "_pending_request_ids", None)
        live_reader = getattr(authority, "_hot_live_states", None)
        bounded_projection = callable(pending_reader) and callable(live_reader)
        pending_before = tuple(pending_reader()) if bounded_projection else ()
        generation_before = int(authority.current_generation)
        if bounded_projection:
            # Event-local no-ops must not scan lifetime state/tombstone/
            # consumption ledgers.  A real mutation needs only the bounded
            # live population and pending queue; fresh IDs are never reused
            # and all births remain live when the transaction opens again.
            states_before = (
                set(live_reader()) if promotions or pending_before else set()
            )
            retired_before: set[str] = set()
            consumptions_before: set[str] = set()
        else:
            # Historical/minimal test authorities predate maintained live
            # indexes.  Normal V2 authorities never take this fallback.
            states_before = set(authority.states)
            retired_before = set(getattr(authority, "retired_tombstones", {}))
            consumptions_before = set(authority.request_consumptions)
        boundary_count_before = len(authority.generation_boundaries)
        # Always invoke authority validation, even when the queue looks empty:
        # a pending REAL event or sealed evaluation must still fail closed.
        prospective = authority.settle_pending_structural_requests(promotions)
        if prospective is None:
            return None
        if bounded_projection:
            child_ids = sorted(set(live_reader()) - states_before)
            retired_cell_ids = list(prospective.retired_cell_ids)
            settled_request_ids = sorted(
                request_id for request_id in pending_before
                if request_id in authority.request_consumptions
            )
        else:
            child_ids = sorted(set(authority.states) - states_before)
            retired_cell_ids = sorted(
                set(getattr(authority, "retired_tombstones", {})) - retired_before
            )
            settled_request_ids = sorted(
                set(authority.request_consumptions) - consumptions_before
            )
        new_boundaries = authority.generation_boundaries[
            boundary_count_before:
        ]
        return {
            "mode": StructuralMode.EVENT_DRIVEN.value,
            "safe_point": "post_consumption_quiescent_real",
            "safe_point_content_blind": True,
            "generation_before": generation_before,
            "generation_after": int(authority.current_generation),
            "settled_request_ids": settled_request_ids,
            "promotion_candidate_ids": sorted(
                request.candidate_id for request in promotions
                if request.candidate_id in authority.boundary_promotion_requests
            ),
            "child_ids": child_ids,
            "retired_cell_ids": retired_cell_ids,
            "live_successor_ids": list(
                authority.live_successor_ids()
                if callable(getattr(authority, "live_successor_ids", None))
                else ()
            ),
            "boundaries": [item.manifest() for item in new_boundaries],
            "prospective_boundary": prospective.manifest(),
        }

    if promotions:
        raise RuntimeError(
            "boundary promotion requires event-driven structural authority"
        )
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
        "mode": StructuralMode.SCHEDULED.value,
        "sealed_boundary": sealed.manifest(),
        "structural_boundary": structural.manifest(),
        "prospective_boundary": prospective.manifest(),
        "sealed_request_count": len(authority.sealed_request_ids),
        "consumptions": consumptions,
        "child_ids": child_ids,
    }


def _boundary_ecology_step(
    authority: Any,
    ecology: ProspectiveBoundaryCandidateEcology,
    *,
    receipt_id: str,
    pre_outcome_state: AvailabilityState,
    excluded_candidate_ids: Iterable[str] = (),
) -> tuple[tuple[BoundaryPromotionRequest, ...], dict[str, Any]]:
    """Commit only the ecology's learner-owned reaction for one REAL event."""

    reference = authority.accepted_real_references[receipt_id]
    observation = _boundary_observation_from_v2_reference(reference)
    if (
        not isinstance(receipt_id, str)
        or observation.receipt_id != receipt_id
    ):
        raise RuntimeError("V2 REAL reference key differs from receipt identity")
    live_states = (
        authority._hot_live_states()
        if callable(getattr(authority, "_hot_live_states", None))
        else {
            cell_id: state
            for cell_id, state in authority.states.items()
            if not getattr(state, "retired", False)
        }
    )
    reaction = ecology.react(
        observation,
        pre_outcome_state=pre_outcome_state.value,
        live_positive_patterns=(
            state.hypothesis.members
            for state in live_states.values()
            if state.hypothesis.polarity is AvailabilityState.AVAILABLE
        ),
        excluded_candidate_ids=excluded_candidate_ids,
    )
    promotion = (
        None
        if reaction.promotion_candidate_id is None
        else _boundary_promotion_request_from_candidate(
            authority,
            ecology,
            reaction.promotion_candidate_id,
        )
    )
    if (
        promotion is not None
        and promotion.candidate_id != reaction.promotion_candidate_id
    ):
        raise RuntimeError("authority substituted the ecology nomination")
    event = reaction.to_manifest()
    event["reaction_digest"] = reaction.digest
    # The exact full-ledger safe-point audit may reject a cheap local
    # nomination.  That is a fail-closed validation of the same candidate,
    # never a host-selected replacement.
    event["promotion_candidate_id"] = (
        None if promotion is None else promotion.candidate_id
    )
    event["promotion_nominated_candidate_id"] = (
        reaction.promotion_candidate_id
    )
    event["promotion_rejected_at_safe_point"] = bool(
        reaction.promotion_candidate_id is not None and promotion is None
    )
    event["active_candidate_count"] = ecology.active_sketch_count
    return (() if promotion is None else (promotion,)), event


def _boundary_observation_from_v2_reference(
    reference: Any,
) -> BoundaryObservation:
    """Project one accepted V2 REAL reference into the local ecology."""

    return BoundaryObservation(
        ordinal=reference.ordinal,
        receipt_id=reference.receipt_id,
        physical_id=reference.stable_physical_interaction_id,
        signal_ids=tuple(reference.ordered_signal_identities),
        signal_roles=tuple(reference.typed_signal_roles),
        observed=reference.observed_outcome,
    )


def _new_boundary_ecology_from_authority_history(
    authority: Any,
    *,
    genome_seed: int,
) -> ProspectiveBoundaryCandidateEcology:
    """Start ecology at the authority's prospective REAL frontier.

    The same-run R0 closure has already consumed a disjoint certification
    tape before R1 begins.  Those accepted prospective receipts belong to the
    lifetime REAL ledger, whereas discovery receipts in ``base.receipts`` do
    not.  Mirroring the prospective prefix while no sketches exist cannot
    bud, refine, or promote anything.  The mirrored prefix lies before every
    later bud's birth frontier, so it may provide remembered proposal context
    but cannot contribute support or certification to that later bud.
    """

    ecology = ProspectiveBoundaryCandidateEcology(
        BoundaryEcologyConfig(genome_seed=int(genome_seed))
    )
    references = authority.accepted_real_references
    observations: list[BoundaryObservation] = []
    for receipt_id in authority.consumed_receipts:
        reference = references.get(receipt_id)
        if reference is None:
            raise RuntimeError(
                "prospective V2 receipt lacks an accepted REAL reference"
            )
        observation = _boundary_observation_from_v2_reference(reference)
        if (
            not isinstance(receipt_id, str)
            or observation.receipt_id != receipt_id
        ):
            raise RuntimeError(
                "prospective V2 receipt key differs from reference identity"
            )
        observations.append(observation)
    ecology.observe_many(observations)
    if ecology.active_sketch_count or ecology.lifetime_birth_count:
        raise RuntimeError("prospective history mirroring created ecology buds")
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=False)
    return ecology


def _boundary_promotion_request_from_candidate(
    authority: Any,
    ecology: ProspectiveBoundaryCandidateEcology,
    candidate_id: str,
) -> BoundaryPromotionRequest | None:
    """Reclose one candidate against all evidence visible at commit time."""

    candidate = ecology.sketches.get(str(candidate_id))
    if (
        candidate is None
        or candidate.state is not SketchLifecycle.ACTIVE
        or not candidate.polarity
    ):
        return None
    # Event-time ranking is deliberately bounded, but the one atomic authority
    # handoff must bind every post-birth REAL read.  This full audit is a
    # structural safe-point operation, not part of recurring observation.
    decision = ecology.audit_promotion_at_safe_point(candidate.sketch_id)
    if not decision.eligible:
        return None
    inspected_ids = tuple(decision.inspected_receipt_ids)
    supporting_ids = tuple(decision.supporting_receipt_ids)
    references = authority.accepted_real_references
    try:
        compact_frontier = max(
            references[item].ordinal for item in inspected_ids
        ) + 1
    except (KeyError, ValueError) as exc:
        # The authority validates the same causal condition, but fail closed
        # here so an ecology record can never become a partially grounded
        # compact request.
        raise ValueError(
            "boundary promotion audit references unknown REAL evidence"
        ) from exc
    inspected_commitment = _compact_set_commitment(
        inspected_ids, exclusive_frontier=compact_frontier
    )
    supporting_commitment = _compact_set_commitment(
        supporting_ids, exclusive_frontier=compact_frontier
    )
    return BoundaryPromotionRequest(
        candidate_id=str(decision.candidate_id),
        members=decision.members,
        fixed_polarity=True,
        triggering_receipt_id=str(decision.triggering_receipt_id),
        # V4 keeps only deterministic witnesses in the request.  The complete
        # sets remain available to the ecology's explicit full-audit call and
        # are reclosed against accepted REAL chronology by the authority.
        supporting_receipt_ids=_bounded_provenance_witnesses(supporting_ids),
        inspected_receipt_ids=_bounded_provenance_witnesses(inspected_ids),
        source_generation=int(authority.current_generation),
        provenance_schema_version=PROVENANCE_COMMITMENT_V4,
        supporting_receipt_commitment=supporting_commitment,
        inspected_receipt_commitment=inspected_commitment,
    )


def _settle_event_local_v2_boundary(
    authority: Any,
    ecology: ProspectiveBoundaryCandidateEcology | None,
    pending_boundary_candidate_ids: Iterable[str],
) -> dict[str, Any] | None:
    """Settle one decision's deferred structural work after TD credit.

    Event-driven authority settlement is intentionally split around the
    decision's learner update.  REAL observation/ecology may nominate a new
    shell, but it cannot retire an existing provider while that same provider
    is still needed by the current all-reply handoff.  The caller invokes this
    helper only after ``credit.transition`` and graph TD application have
    returned successfully.  The candidate-ID set is per decision, never an
    epoch batch; an empty set still lets native authority requests settle.
    """

    promotion_requests: list[BoundaryPromotionRequest] = []
    if ecology is not None:
        for candidate_id in sorted(set(map(str, pending_boundary_candidate_ids))):
            request = _boundary_promotion_request_from_candidate(
                authority,
                ecology,
                candidate_id,
            )
            if request is not None:
                promotion_requests.append(request)
    structural = _advance_v2_structural_frontier(
        authority,
        promotions=promotion_requests,
    )
    if structural is None:
        return None
    if ecology is not None:
        for request in promotion_requests:
            if request.candidate_id not in authority.boundary_promotion_requests:
                raise RuntimeError(
                    "event-local boundary promotion was not committed"
                )
            ecology.mark_promoted(request.candidate_id)
    return structural


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


def _verify_boundary_ecology_alignment(
    authority: Any,
    ecology: ProspectiveBoundaryCandidateEcology,
    *,
    roundtrip: bool,
) -> None:
    """Require exact ecology/V2 REAL-ledger identity at resumable boundaries."""

    if set(ecology.observations) != set(authority.consumed_receipts):
        raise RuntimeError("boundary ecology ledger differs from V2 REAL history")
    for receipt_id, observation in ecology.observations.items():
        reference = authority.accepted_real_references.get(receipt_id)
        if reference is None or (
            observation.ordinal != reference.ordinal
            or observation.physical_id
            != reference.stable_physical_interaction_id
            or observation.signal_ids
            != tuple(sorted(reference.ordered_signal_identities))
            or observation.signal_roles
            != tuple(sorted(reference.typed_signal_roles))
            or observation.observed is not reference.observed_outcome
        ):
            raise RuntimeError(
                "boundary ecology observation differs from V2 REAL reference"
            )
    if roundtrip:
        restored = ProspectiveBoundaryCandidateEcology.loads(ecology.dumps())
        if restored.manifest() != ecology.manifest():
            raise RuntimeError("boundary ecology serialization roundtrip mismatch")


def _adaptive_positive_lineage_audit(
    authority: Any | None,
    ecology: ProspectiveBoundaryCandidateEcology | None,
) -> dict[str, Any]:
    """Build the final, report-only audit of adaptive positive lineages.

    Boundary ecology and the V2 authority intentionally keep different
    ledgers: ecology owns cheap local candidate history, while authority owns
    committed cells and certification evidence.  This helper joins those two
    ledgers without changing either one.  The join is deliberately fail-closed
    because a report which silently drops a candidate or mixes discovery and
    certification evidence would be more misleading than no report.

    The returned rows are canonical JSON-shaped dictionaries.  A boundary
    promotion request is the root of one row; its authority descendants are
    collected recursively through ``lineage_parent_id`` and ordered by depth,
    source generation, and cell identity.  Certification is post-birth only:
    any certification receipt at or before a node's birth frontier is a
    report integrity failure, not a recoverable metric anomaly.
    """

    disabled = {
        "enabled": False,
        "lineage_count": 0,
        "node_count": 0,
        "promoted_candidate_count": 0,
        "certified_node_count": 0,
        "live_node_count": 0,
        "retired_node_count": 0,
        "certification_receipt_count": 0,
        "postbirth_certification_receipt_count": 0,
        "certification_leak_count": 0,
        "all_certification_disjoint": True,
        "all_certification_postbirth": True,
        "rows": [],
    }
    if authority is None or ecology is None:
        return disabled

    requests = getattr(authority, "boundary_promotion_requests", None)
    states = getattr(authority, "states", None)
    references = getattr(authority, "accepted_real_references", None)
    if not isinstance(requests, Mapping):
        raise RuntimeError(
            "adaptive positive lineage audit requires a boundary promotion ledger"
        )
    if not isinstance(states, Mapping):
        raise RuntimeError(
            "adaptive positive lineage audit requires authority states"
        )
    if not isinstance(references, Mapping):
        raise RuntimeError(
            "adaptive positive lineage audit requires accepted REAL references"
        )

    observations = ecology.observations
    sketches = ecology.sketches
    tombstones = ecology.tombstones

    def _canonical_ids(values: Iterable[str], label: str) -> tuple[str, ...]:
        items = tuple(values)
        if any(not isinstance(item, str) or not item for item in items):
            raise RuntimeError(f"adaptive lineage {label} contains an invalid receipt ID")
        if len(set(items)) != len(items):
            raise RuntimeError(f"adaptive lineage {label} contains duplicate receipts")
        return tuple(sorted(items))

    known_receipt_ids = set(references)
    ordered_references = tuple(sorted(
        references.values(),
        key=lambda item: (int(item.ordinal), str(item.receipt_id)),
    ))

    ecology_receipt_ids = set(observations)

    def _check_receipts(
        values: Iterable[str],
        label: str,
        *,
        require_ecology_observation: bool = False,
    ) -> tuple[str, ...]:
        ids = _canonical_ids(values, label)
        unknown = set(ids).difference(known_receipt_ids)
        if unknown:
            raise RuntimeError(
                f"adaptive lineage {label} references unknown REAL receipt(s): "
                f"{sorted(unknown)}"
            )
        if require_ecology_observation:
            unobserved = set(ids).difference(ecology_receipt_ids)
            if unobserved:
                raise RuntimeError(
                    f"adaptive lineage {label} references receipt(s) absent "
                    f"from ecology REAL observations: {sorted(unobserved)}"
                )
        return ids

    # Ecology's promoted tombstones are the only acceptable source of a
    # committed positive candidate.  Check both directions so an orphaned
    # ecology promotion cannot disappear from the final authority report.
    promoted_ecology_ids: set[str] = set()
    for candidate_id, candidate in sorted(sketches.items()):
        state = SketchLifecycle(candidate.state)
        if (
            state is SketchLifecycle.DORMANT
            and candidate.retirement_reason == "promoted"
        ):
            if tombstones.get(candidate_id) != candidate:
                raise RuntimeError(
                    "adaptive lineage promoted ecology sketch lacks its exact tombstone"
                )
            promoted_ecology_ids.add(str(candidate_id))
    request_ids = {str(item) for item in requests}
    if promoted_ecology_ids != request_ids:
        raise RuntimeError(
            "adaptive lineage ecology/authority promotion identity mismatch: "
            f"ecology={sorted(promoted_ecology_ids)} authority={sorted(request_ids)}"
        )

    children_by_parent: dict[str, list[str]] = {}
    for cell_id, state in sorted(states.items()):
        parent_id = getattr(state.hypothesis, "lineage_parent_id", None)
        if parent_id is not None:
            children_by_parent.setdefault(str(parent_id), []).append(str(cell_id))

    rows: list[dict[str, Any]] = []
    total_nodes = 0
    certified_nodes = 0
    live_nodes = 0
    retired_nodes = 0
    certification_receipt_count = 0
    postbirth_certification_receipt_count = 0
    certification_leak_count = 0
    all_disjoint = True
    all_postbirth = True

    for candidate_id, request in sorted(
        requests.items(),
        key=lambda item: (item[1].request_digest, str(item[0])),
    ):
        candidate_id = str(candidate_id)
        candidate = sketches.get(candidate_id)
        if candidate is None:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} lacks an ecology sketch"
            )
        if (
            candidate.state is not SketchLifecycle.DORMANT
            or candidate.retirement_reason != "promoted"
            or candidate.polarity is not True
        ):
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} was not a positive ecology promotion"
            )
        if request.fixed_polarity is not AvailabilityState.AVAILABLE:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} is not AVAILABLE"
            )
        if tuple(candidate.members) != tuple(request.members):
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} member mismatch"
            )
        if candidate.triggering_receipt_id != request.triggering_receipt_id:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} trigger mismatch"
            )

        ecology_supporting = _check_receipts(
            candidate.supporting_receipt_ids,
            f"{candidate_id}.ecology_supporting",
            require_ecology_observation=True,
        )
        ecology_inspected = _check_receipts(
            candidate.read_receipt_ids,
            f"{candidate_id}.ecology_inspected",
            require_ecology_observation=True,
        )
        authority_supporting = _check_receipts(
            request.supporting_receipt_ids,
            f"{candidate_id}.authority_supporting",
            require_ecology_observation=True,
        )
        authority_inspected = _check_receipts(
            request.inspected_receipt_ids,
            f"{candidate_id}.authority_inspected",
            require_ecology_observation=True,
        )
        trigger_observation = observations.get(request.triggering_receipt_id)
        if (
            trigger_observation is None
            or trigger_observation.observed is not True
            or request.triggering_receipt_id not in ecology_receipt_ids
        ):
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} lacks a positive REAL trigger"
            )
        if candidate.birth_ordinal != trigger_observation.ordinal:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} birth ordinal differs from trigger"
            )
        compact_promotion = request.provenance_schema_version == (
            PROVENANCE_COMMITMENT_V4
        )
        if compact_promotion:
            inspected_commitment = request.inspected_receipt_commitment
            supporting_commitment = request.supporting_receipt_commitment
            if inspected_commitment is None or supporting_commitment is None:
                raise RuntimeError(
                    f"adaptive lineage promotion {candidate_id} lacks compact evidence commitments"
                )
            trigger_reference = references[request.triggering_receipt_id]
            frontier = int(inspected_commitment.exclusive_frontier)
            committed_interval = tuple(
                reference
                for reference in ordered_references
                if int(trigger_reference.ordinal)
                <= int(reference.ordinal)
                < frontier
            )
            committed_inspected_ids = tuple(
                str(reference.receipt_id)
                for reference in committed_interval
            )
            if (
                request.triggering_receipt_id not in committed_inspected_ids
                or _compact_set_commitment(
                    committed_inspected_ids,
                    exclusive_frontier=frontier,
                )
                != inspected_commitment
            ):
                raise RuntimeError(
                    f"adaptive lineage promotion {candidate_id} has an incomplete inspected commitment"
                )
            committed_support_ids = tuple(
                str(reference.receipt_id)
                for reference in committed_interval
                if reference.observed_outcome is True
                and set(request.members).issubset(
                    reference.ordered_signal_identities
                )
            )
            if (
                request.triggering_receipt_id not in committed_support_ids
                or _compact_set_commitment(
                    committed_support_ids,
                    exclusive_frontier=frontier,
                )
                != supporting_commitment
            ):
                raise RuntimeError(
                    f"adaptive lineage promotion {candidate_id} has an incomplete supporting commitment"
                )
        elif request.triggering_receipt_id not in authority_inspected:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} omits its trigger from inspected evidence"
            )

        # The identity formula is part of the authority contract.  Deriving
        # it here instead of trusting a report field makes orphaned/mislinked
        # lineage rows visible.
        root_child_id = f"v2_adaptive_boundary_{request.request_digest}"
        root_state = states.get(root_child_id)
        if root_state is None:
            raise RuntimeError(
                f"adaptive lineage promotion {candidate_id} lacks root child {root_child_id}"
            )
        root_hypothesis = root_state.hypothesis
        if (
            tuple(root_hypothesis.members) != tuple(request.members)
            or root_hypothesis.polarity is not AvailabilityState.AVAILABLE
            or root_hypothesis.source_generation != request.source_generation + 1
            or root_hypothesis.lineage_parent_id is not None
            or root_hypothesis.specialization_depth != 0
            or root_hypothesis.triggering_receipt_id != request.triggering_receipt_id
        ):
            raise RuntimeError(
                f"adaptive lineage root child {root_child_id} does not match its promotion request"
            )

        ordered_node_ids: list[str] = []
        seen_node_ids: set[str] = set()
        pending = [root_child_id]
        while pending:
            cell_id = pending.pop(0)
            if cell_id in seen_node_ids:
                raise RuntimeError(
                    f"adaptive lineage {candidate_id} contains a repeated/cyclic authority descendant"
                )
            seen_node_ids.add(cell_id)
            state = states.get(cell_id)
            if state is None:
                raise RuntimeError(
                    f"adaptive lineage {candidate_id} references missing authority cell {cell_id}"
                )
            ordered_node_ids.append(cell_id)
            children = sorted(
                children_by_parent.get(cell_id, ()),
                key=lambda child_id: (
                    states[child_id].hypothesis.specialization_depth,
                    states[child_id].hypothesis.source_generation,
                    child_id,
                ),
            )
            pending.extend(children)

        node_rows: list[dict[str, Any]] = []
        for cell_id in ordered_node_ids:
            state = states[cell_id]
            hypothesis = state.hypothesis
            discovery_ids = _check_receipts(
                hypothesis.discovery_exclusion_receipt_ids,
                f"{cell_id}.discovery_exclusion",
            )
            certification_ids = _check_receipts(
                state.certification_receipt_ids,
                f"{cell_id}.certification",
            )
            if tuple(sorted(set(discovery_ids))) != discovery_ids:
                raise RuntimeError(
                    f"adaptive lineage {cell_id} discovery exclusion is not canonical"
                )
            if cell_id != root_child_id:
                parent_id = hypothesis.lineage_parent_id
                if parent_id not in seen_node_ids:
                    raise RuntimeError(
                        f"adaptive lineage {cell_id} parent is outside its root lineage"
                    )
                parent_state = states[parent_id]
                if hypothesis.specialization_depth != (
                    parent_state.hypothesis.specialization_depth + 1
                ):
                    raise RuntimeError(
                        f"adaptive lineage {cell_id} depth is not parent-plus-one"
                    )
            ref_ordinals = {
                receipt_id: int(references[receipt_id].ordinal)
                for receipt_id in certification_ids
            }
            birth_frontier = int(hypothesis.birth_frontier)
            postbirth_ids = tuple(sorted(
                receipt_id
                for receipt_id, ordinal in ref_ordinals.items()
                if ordinal > birth_frontier
            ))
            leak_ids = tuple(sorted(
                receipt_id
                for receipt_id, ordinal in ref_ordinals.items()
                if receipt_id in set(discovery_ids) or ordinal <= birth_frontier
            ))
            disjoint = not bool(set(certification_ids).intersection(discovery_ids))
            all_node_postbirth = not leak_ids and len(postbirth_ids) == len(certification_ids)
            all_disjoint = all_disjoint and disjoint
            all_postbirth = all_postbirth and all_node_postbirth
            certification_receipt_count += len(certification_ids)
            postbirth_certification_receipt_count += len(postbirth_ids)
            certification_leak_count += len(leak_ids)
            is_retired = bool(getattr(state, "retired", False))
            if is_retired:
                retired_nodes += 1
            else:
                live_nodes += 1
            certified_nodes += int(bool(state.prospectively_certified))
            node_rows.append({
                "cell_id": cell_id,
                "parent_cell_id": hypothesis.lineage_parent_id,
                "specialization_depth": int(hypothesis.specialization_depth),
                "source_generation": int(hypothesis.source_generation),
                "polarity": hypothesis.polarity.value,
                "live": not is_retired,
                "retired": is_retired,
                "live_retired": "RETIRED" if is_retired else "LIVE",
                "certified": bool(state.prospectively_certified),
                "support": int(state.support),
                "support_receipt_ids": list(_check_receipts(
                    state.support_receipt_ids,
                    f"{cell_id}.support",
                )),
                "contradictions": int(state.contradictions),
                "contradiction_receipt_ids": list(_check_receipts(
                    state.contradiction_receipt_ids,
                    f"{cell_id}.contradiction",
                )),
                "birth_frontier": birth_frontier,
                "discovery_exclusion_receipt_ids": list(discovery_ids),
                "certification_receipt_ids": list(certification_ids),
                "postbirth_certification_receipt_ids": list(postbirth_ids),
                "certification_leak_receipt_ids": list(leak_ids),
                "certification_discovery_disjoint": disjoint,
                "all_certification_postbirth": all_node_postbirth,
            })
            total_nodes += 1

        rows.append({
            "candidate_id": candidate_id,
            "members": list(candidate.members),
            "ecology_parent_sketch_id": candidate.parent_sketch_id,
            "ecology_refinement_source_receipt_id": (
                candidate.refinement_source_receipt_id
            ),
            "ecology_triggering_receipt_id": candidate.triggering_receipt_id,
            "ecology_birth_ordinal": int(candidate.birth_ordinal),
            "ecology_supporting_receipt_ids": list(ecology_supporting),
            "ecology_inspected_receipt_ids": list(ecology_inspected),
            "authority_supporting_receipt_ids": list(authority_supporting),
            "authority_inspected_receipt_ids": list(authority_inspected),
            "authority_supporting_receipt_commitment": (
                None
                if request.supporting_receipt_commitment is None
                else request.supporting_receipt_commitment.manifest()
            ),
            "authority_inspected_receipt_commitment": (
                None
                if request.inspected_receipt_commitment is None
                else request.inspected_receipt_commitment.manifest()
            ),
            "root_child_id": root_child_id,
            "root_child_generation": int(root_hypothesis.source_generation),
            "promotion_request_digest": request.request_digest,
            "nodes": node_rows,
        })

    if certification_leak_count or not all_disjoint or not all_postbirth:
        raise RuntimeError(
            "adaptive positive lineage certification reused discovery or "
            "pre-birth evidence"
        )

    return {
        "enabled": True,
        "lineage_count": len(rows),
        "node_count": total_nodes,
        "promoted_candidate_count": len(rows),
        "certified_node_count": certified_nodes,
        "live_node_count": live_nodes,
        "retired_node_count": retired_nodes,
        "certification_receipt_count": certification_receipt_count,
        "postbirth_certification_receipt_count": postbirth_certification_receipt_count,
        "certification_leak_count": certification_leak_count,
        "all_certification_disjoint": all_disjoint,
        "all_certification_postbirth": all_postbirth,
        "rows": rows,
    }


def _v2_r0_observe_training_successor(
    authority: Any,
    board: chess.Board,
    *,
    seen_predecessor_fens: set[str],
    frame_id: str,
    frame_session: Any | None = None,
    expected_virtual_actuation: Mapping[str, Any] | None = None,
    boundary_ecology: ProspectiveBoundaryCandidateEcology | None = None,
    pending_boundary_candidate_ids: set[str] | None = None,
    r0_core_graph: NativeReConKRKGraph | None = None,
    r0_core_gate: OutcomeCalibratedPrototypeGate | None = None,
    r0_core_triplet_ids: frozenset[str] | None = None,
) -> tuple[bool, dict[str, Any], bool, dict[str, Any] | None]:
    """Classify before one unique REAL result, then learn for later events."""

    core_supplied = bool(
        r0_core_graph is not None or r0_core_gate is not None
        or r0_core_triplet_ids is not None
    )
    core_enabled = bool(
        r0_core_graph is not None
        and r0_core_gate is not None
        and r0_core_triplet_ids is not None
    )
    if core_supplied and not core_enabled:
        raise ValueError(
            "training successor core routing requires graph, gate, and triplet ids"
        )
    if core_enabled and not r0_core_triplet_ids.issubset(
        r0_core_graph.triplet_ids
    ):
        raise ValueError("protected R0 core triplet ids are not in its graph")

    def require_virtual_real_actuation_parity(
        *,
        selected_move: str | None,
        selected_triplet: str | None,
        selected_option_identity: str | None,
        exact_action_pattern_id: str | None,
    ) -> None:
        if expected_virtual_actuation is None:
            return
        expected = {
            "selected_move": expected_virtual_actuation.get(
                "selected_move"
            ),
            "selected_triplet": expected_virtual_actuation.get(
                "selected_triplet"
            ),
            "selected_option_identity": expected_virtual_actuation.get(
                "selected_option_identity"
            ),
            "exact_action_pattern_id": expected_virtual_actuation.get(
                "exact_action_pattern_id"
            ),
        }
        observed = {
            "selected_move": selected_move,
            "selected_triplet": selected_triplet,
            "selected_option_identity": selected_option_identity,
            "exact_action_pattern_id": exact_action_pattern_id,
        }
        if observed != expected:
            raise RuntimeError(
                "VIRTUAL/REAL child actuation parity mismatch: "
                + json.dumps(
                    {"expected": expected, "observed": observed},
                    sort_keys=True,
                )
            )

    def add_core_routing(response: dict[str, Any]) -> None:
        provider = response.get("provider")
        local_provider = response.get("local_provider")
        if isinstance(provider, Mapping):
            provider_kind = str(response.get("provider_kind") or "")
            direct = bool(provider_kind == "native_direct_outcome_cell")
            provider_available = bool(response.get("available", False))
            response["core_routing"] = {
                "available": bool(direct and provider_available),
                "effective_available": provider_available,
                "local_available": bool(direct and provider_available),
                "response": dict(response),
                "local_response": dict(response),
                "v2_grounding": response.get("authority_grounding"),
                "v2_fallback_available": bool(available),
                "action_parity": True,
                "core_selected_move": response.get("selected_move"),
                "v2_selected_move": response.get("selected_move"),
                "effective_source": provider_kind,
            }
            return
        if not core_enabled:
            return
        _core_local_available, local_response = _protected_core_r0_available(
            r0_core_graph,
            r0_core_gate,
            board,
            allowed_triplets=r0_core_triplet_ids,
            authority=authority,
            frame_session=frame_session,
        )
        effective_core_available, effective_response, v2_grounding = (
            _core_response_for_v2_training(authority, local_response)
        )
        core_move = local_response.get("selected_move")
        v2_move = response.get("selected_move")
        action_parity = bool(
            core_move is not None
            and v2_move is not None
            and str(core_move) == str(v2_move)
        )
        if effective_core_available and not action_parity:
            raise RuntimeError(
                "protected R0 core action differs from V2 REAL actuation"
            )
        raw_v2_available = bool(available)
        v2_fallback_available = bool(
            raw_v2_available
            and v2_grounding.get("explicit_grounding_valid", False)
        )
        response["core_routing"] = {
            "available": bool(effective_core_available),
            "effective_available": bool(
                effective_core_available or v2_fallback_available
            ),
            "local_available": bool(_core_local_available),
            "response": effective_response,
            "local_response": local_response,
            "v2_grounding": v2_grounding,
            "v2_fallback_available": v2_fallback_available,
            "action_parity": action_parity,
            "core_selected_move": core_move,
            "v2_selected_move": v2_move,
            "effective_source": (
                "frozen_r0_local_competence_gate"
                if effective_core_available
                else (
                    "v2_grounded_descendant"
                    if v2_fallback_available
                    else "unknown"
                )
            ),
        }

    predecessor_fen = board.fen()
    if predecessor_fen in seen_predecessor_fens:
        available, response = _v2_r0_available(
            authority,
            board,
            frame_id=f"{frame_id}:duplicate-virtual",
            frame_session=frame_session,
        )
        selected_move = response.get("selected_move")
        require_virtual_real_actuation_parity(
            selected_move=(
                None if selected_move is None else str(selected_move)
            ),
            selected_triplet=response.get("selected_triplet"),
            selected_option_identity=response.get(
                "selected_option_identity"
            ),
            exact_action_pattern_id=response.get(
                "exact_action_pattern_id"
            ),
        )
        actual_mate = False
        if selected_move is not None:
            move = chess.Move.from_uci(str(selected_move))
            actual_mate = _execute_white_and_observe(board, move) == "mate"
        response["observed_immediate_mate"] = actual_mate
        response["duplicate_virtual_query"] = True
        # This query is outcome-free from the authority's perspective; the
        # actual-mate bit is only used as the duplicate's already-known
        # world-outcome check.  Core routing itself reads no outcome.
        add_core_routing(response)
        return available, response, True, None

    frame = FrameContext(
        frame_id=str(frame_id),
        kind=FrameKind.REAL,
        values={"board": board.copy(stack=False)},
    )
    pending, trace = (
        authority.open_real_event(
            frame,
            expected_actuation=expected_virtual_actuation,
        )
        if frame_session is None
        else authority.open_real_event(
            frame,
            frame_session=frame_session,
            expected_actuation=expected_virtual_actuation,
        )
    )
    # Capture shell authority before observing this outcome.  The same REAL
    # receipt may strengthen an existing provider, but a cell first certified
    # by this receipt cannot bootstrap the transition that certified it.
    native_provider_records_fn = getattr(
        authority,
        "native_provider_records",
        None,
    )
    pre_outcome_shell_records = (
        tuple(native_provider_records_fn(pending.pre_outcome_classification))
        if callable(native_provider_records_fn)
        else ()
    )
    pre_outcome_shell_provider = (
        copy.deepcopy(pre_outcome_shell_records[0])
        if pre_outcome_shell_records
        else None
    )
    selected_move = chess.Move.from_uci(trace.actuation.move_uci)
    r0 = getattr(authority.base, "r0", None)
    provenance = getattr(r0, "provenance", None)
    selected_triplet = str(
        getattr(
            trace.actuation,
            "selected_triplet_id",
            trace.actuation.option_identity,
        )
    )
    direct_provider_ids = tuple(
        getattr(r0, "direct_provider_ids", ())
    )
    r0_graph = getattr(r0, "graph", None)
    exact_selected_pattern = (
        None
        if r0_graph is None
        else _triplet_id(
            *_triplet_keys(
                board,
                selected_move,
                key_mode=r0_graph.config.key_mode,
            )
        )
    )
    local_provider = (
        authority.native_direct_provider_response(exact_selected_pattern)
        if (
            direct_provider_ids
            and exact_selected_pattern in direct_provider_ids
            and callable(
                getattr(authority, "native_direct_provider_response", None)
            )
        )
        else None
    )
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
    classification = pending.pre_outcome_classification.to_manifest()
    shell_provider: Mapping[str, Any] | None = None
    if isinstance(pre_outcome_shell_provider, Mapping):
        provider_id = str(pre_outcome_shell_provider.get("cell_id", ""))
        provider_resolver = getattr(
            authority,
            "native_provider_response",
            None,
        )
        current_provider = (
            provider_resolver(provider_id)
            if provider_id and callable(provider_resolver)
            else None
        )
        if (
            isinstance(current_provider, Mapping)
            and current_provider.get("cell_id") == provider_id
            and current_provider.get("hypothesis_digest")
            == pre_outcome_shell_provider.get("hypothesis_digest")
            and int(current_provider.get("certification_receipt_count", -1))
            >= int(
                pre_outcome_shell_provider.get(
                    "certification_receipt_count", 0
                )
            )
        ):
            shell_provider = pre_outcome_shell_provider
    provider = local_provider if local_provider is not None else shell_provider
    provider_kind = (
        None if provider is None else str(provider.get("provider_kind", ""))
    )
    raw_grounded = getattr(provenance, "grounded", None)
    authority_grounded, authority_grounding = _v2_grounding_audit(authority)
    grounded = bool(
        provider is not None and authority_grounded
        if direct_provider_ids
        else (
            type(raw_grounded) is bool
            and raw_grounded
            and authority_grounded
        )
    )
    available = bool(
        grounded
        and (
            local_provider is not None
            or str(classification["state"]).lower() == "available"
        )
    )
    response = {
        "selected_move": selected_move.uci(),
        "selected_triplet": selected_triplet,
        "exact_selected_pattern": exact_selected_pattern,
        "selected_triplet_is_exact_pattern": bool(
            selected_triplet == exact_selected_pattern
        ),
        "selected_option_identity": str(trace.actuation.option_identity),
        "observed_immediate_mate": successor.is_checkmate(),
        "available": available,
        "availability_source": "v2_prospective_pre_outcome_graph_emission",
        "classification": classification,
        # Preserve the provider's raw legacy value for audit while the local
        # path exposes only its computed strict boolean.  ``available`` above
        # always uses the fail-closed normalized value.
        "grounded": (
            grounded if direct_provider_ids else raw_grounded
        ),
        "grounding_source": (
            None
            if provider is None
            else provider["grounding_source"]
        ) if direct_provider_ids else getattr(
            provenance, "grounding_source", None
        ),
        "authority_grounding": authority_grounding,
        "provider": None if provider is None else dict(provider),
        "provider_kind": provider_kind,
        "provider_id": (
            None if provider is None else str(provider["cell_id"])
        ),
        "provider_value": (
            0.0
            if provider is None
            else float(provider["expected_value"])
        ),
        "provider_confidence": (
            0.0
            if provider is None
            else float(provider["confidence"])
        ),
        "local_provider": (
            None if local_provider is None else dict(local_provider)
        ),
        "pre_outcome_shell_provider": (
            None
            if pre_outcome_shell_provider is None
            else dict(pre_outcome_shell_provider)
        ),
        "certification_emission": emission.manifest(),
        "virtual_frame_terminal_grounding_granted": False,
    }
    add_core_routing(response)
    promotions: tuple[BoundaryPromotionRequest, ...] = ()
    ecology_event: dict[str, Any] | None = None
    if boundary_ecology is not None:
        raw_pre_outcome_state = pending.pre_outcome_classification.state
        if isinstance(raw_pre_outcome_state, AvailabilityState):
            effective_pre_outcome_state = raw_pre_outcome_state
        else:
            try:
                effective_pre_outcome_state = AvailabilityState(
                    str(raw_pre_outcome_state).strip().lower()
                )
            except ValueError:
                # Unknown/malformed provider state must remain fail-closed for
                # ecology birth decisions; the raw classification is retained
                # unchanged in the response and receipt.
                effective_pre_outcome_state = AvailabilityState.UNKNOWN
        core_routing = response.get("core_routing") or {}
        if bool(core_routing.get("effective_available", False)):
            # A known local capability is not a surprise boundary success,
            # whether supplied by an exact R0 pattern or a certified shell.
            # Preserve the raw V2 classification in the response above; only
            # the ecology's birth trigger sees the effective local authority.
            effective_pre_outcome_state = AvailabilityState.AVAILABLE
        response["effective_pre_outcome_state"] = (
            effective_pre_outcome_state.value
            if isinstance(effective_pre_outcome_state, AvailabilityState)
            else str(effective_pre_outcome_state)
        )
        promotions, ecology_event = _boundary_ecology_step(
            authority,
            boundary_ecology,
            receipt_id=receipt.receipt_id,
            pre_outcome_state=effective_pre_outcome_state,
            excluded_candidate_ids=(
                ()
                if pending_boundary_candidate_ids is None
                else pending_boundary_candidate_ids
            ),
        )
        response["boundary_ecology"] = ecology_event
    if pending_boundary_candidate_ids is not None:
        pending_boundary_candidate_ids.update(
            item.candidate_id for item in promotions
        )
        structural = None
    else:
        structural = _advance_v2_structural_frontier(
            authority,
            promotions=promotions,
        )
    if promotions and pending_boundary_candidate_ids is None:
        promoted = promotions[0]
        if promoted.candidate_id not in authority.boundary_promotion_requests:
            raise RuntimeError("eligible boundary promotion was not committed")
        boundary_ecology.mark_promoted(promoted.candidate_id)
        if ecology_event is not None:
            ecology_event["promotion_committed"] = True
            ecology_event["promoted_child_ids"] = (
                [] if structural is None else list(structural["child_ids"])
            )
            ecology_event["active_candidate_count"] = (
                boundary_ecology.active_sketch_count
            )
    elif promotions and ecology_event is not None:
        ecology_event["promotion_queued"] = True
    # Duplicate suppression is operational state, not evidence.  Commit it
    # only after provider projection and the event-local structural decision
    # have succeeded.  Refinement parents deliberately remain REFINING here;
    # ``observe`` closes them only when their local event cap is exhausted (or
    # capacity pressure evicts them).  A caller may still invoke the retained
    # ``settle_refinements`` compatibility helper explicitly, but production
    # training never batches or epoch-settles this lifecycle.
    seen_predecessor_fens.add(predecessor_fen)
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
        "probe_split": "r0_validation",
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
