"""Bounded, viewed development integration of V2 R0 authority into R1.

This is a one-seed engineering shot.  It creates a new deterministic balanced
KRK pool, permanently labels it viewed/non-scientific, starts the curriculum
with no learned state, and derives the V2 child only from that same run's
training-only R0 graph and grounded outcomes.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
import traceback
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.learning import IntrinsicCreditEngine
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeR0Organism,
)
from .native_competence_envelope import (
    CompetenceEnvelopeConfig,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from .native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    NativeIntrinsicCurriculumResult,
    R0_COMPETENCE_ID,
    R1DevelopmentCeilingReached,
    V2_PROSPECTIVE_AVAILABILITY,
    _Pools,
    _hash_json,
    _source_identity,
    run_native_intrinsic_curriculum,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
    V2Mode,
)
from .native_single_graph_curriculum import NativeReConKRKGraph
from .native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


SCHEMA_VERSION = "native_intrinsic_v2_r0_r1_development.v1"
DEVELOPMENT_LABEL = "DEVELOPMENT_VIEWED_NOT_SCIENTIFIC"
DEFAULT_SEED = 2026082801
DEVELOPMENT_FEN_FULLMOVE_BASE = 900_000
DISCOVERY_POSITIVE_COUNT = 16
DISCOVERY_NEGATIVE_COUNT = 16
DISCOVERY_TAPE_COUNT = DISCOVERY_POSITIVE_COUNT + DISCOVERY_NEGATIVE_COUNT
PROSPECTIVE_EVENTS_BEFORE_STRUCTURE = 64
DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/development/"
    "native_intrinsic_v2_r0_r1_seed_2026082801"
)


def _development_source_identity() -> dict[str, Any]:
    identity = dict(_source_identity())
    identity["development_runner_sha256"] = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    return identity


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _neutral_discovery_tape(source_fens: Sequence[str]) -> tuple[str, ...]:
    """Select and order discovery rows from content, without pool labels.

    The source is intentionally treated as a multiset.  A stable digest rank
    makes both the selected rows and their authority event order independent
    of the named training pool (and of each pool's input order).  Equal FENs
    remain repeated rows in the tape, preserving multiplicity.
    """

    if len(source_fens) < DISCOVERY_TAPE_COUNT:
        raise ValueError("V2 discovery source is too small for fixed 32 rows")
    ranked = sorted(
        (
            hashlib.sha256(
                b"native-intrinsic-v2-neutral-discovery|"
                + fen.encode("utf-8")
            ).digest(),
            fen,
        )
        for fen in source_fens
    )
    return tuple(fen for _digest, fen in ranked[:DISCOVERY_TAPE_COUNT])


def _mint_discovery_receipts(
    source: TraceNativeCompetenceOrganism,
    fens: Sequence[str],
) -> tuple[Any, ...]:
    terminal = source.completion_terminal()
    receipts = []
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        actuation, trace = source.r0.emit_action_with_trace(
            FrameContext(
                frame_id=f"native-intrinsic-v2-discovery:{index:04d}",
                kind=FrameKind.REAL,
                values={"board": board},
            )
        )
        if actuation is None or trace is None:
            raise RuntimeError(f"frozen R0 emitted no discovery action at row {index}")
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        receipts.append(terminal.mint(trace, board, successor))
    return tuple(receipts)


def build_same_run_v2_r0_authority(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
) -> tuple[NativeProspectiveAuthorityV2, Mapping[str, Any]]:
    """Derive a fail-closed prospective child from training-only R0 evidence."""

    if config.r0_availability_mode != V2_PROSPECTIVE_AVAILABILITY:
        raise ValueError("same-run V2 factory requires v2_prospective mode")
    training_source_fens = tuple(
        (*pools.r0_train, *pools.gate_train_decoys)
    )
    if len(training_source_fens) < DISCOVERY_TAPE_COUNT:
        raise ValueError("V2 discovery source is too small for fixed 32 rows")
    if not credit.states[R0_COMPETENCE_ID].mature:
        raise RuntimeError("V2 child construction requires mature R0 credit")

    graph_copy = copy.deepcopy(graph)
    credit_copy = copy.deepcopy(credit)
    pool_manifest = pools.manifest()
    training_source_digest = _hash_json(tuple(sorted(training_source_fens)))
    r0 = NativeR0Organism(
        graph=graph_copy,
        credit=credit_copy,
        provenance=FrozenCompetenceProvenance.from_credit(
            credit_copy, R0_COMPETENCE_ID
        ),
        frozen_triplet_ids=frozenset(graph_copy.triplet_ids),
        source_manifest={
            "kind": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "same_run_empty_start_r0": True,
            "curriculum_seed": int(config.seed),
            "training_source_fens_sha256": training_source_digest,
            "training_only_discovery": True,
        },
    )
    envelope_seed = int(config.seed) ^ 0x56325052
    envelope_config = CompetenceEnvelopeConfig(selection_seed=envelope_seed)
    source = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=envelope_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=envelope_seed,
            completion_terminal_identity="mate",
            receipt_issuer_identity="native_intrinsic_v2_development_adapter.v1",
            receipt_capability_key=(
                "native-intrinsic-v2-development:"
                + hashlib.sha256(str(config.seed).encode("utf-8")).hexdigest()
            ),
        ),
    )
    source.open_prospective_discovery_epoch()
    ordered_fens = _neutral_discovery_tape(training_source_fens)
    receipts = _mint_discovery_receipts(source, ordered_fens)
    source.grow_from_grounded_receipts(
        receipts,
        finalize=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW,
    )
    adaptive = bool(config.r0_boundary_ecology_enabled)
    absolute_structural_frontier = (
        source._next_event_ordinal + PROSPECTIVE_EVENTS_BEFORE_STRUCTURE
    )
    authority = NativeProspectiveAuthorityV2.from_organism(
        source,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_epoch_schedule=(
            () if adaptive else (absolute_structural_frontier,)
        ),
        structural_mode=(
            StructuralMode.EVENT_DRIVEN
            if adaptive else StructuralMode.SCHEDULED
        ),
    )
    frozen_candidates = authority.close_nomination()
    dormant_shadow_count = sum(
        cell.state is StemCellState.DORMANT and cell.is_shadow
        for cell in authority.base.envelope.cells.values()
    )
    if not frozen_candidates:
        raise RuntimeError("same-run V2 discovery nominated no candidates")
    if dormant_shadow_count == 0:
        raise RuntimeError("same-run V2 discovery retained no specialization shadow")
    authority.verify_full_history_boundary(
        "native-intrinsic-v2-discovery-boundary"
    )
    payload = authority.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    if restored.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError("initial same-run V2 authority failed roundtrip parity")
    expected_predecessor_fens = tuple(
        chess.Board(fen).fen() for fen in ordered_fens
    )
    actual_predecessor_fens = tuple(
        receipt.predecessor_fen for receipt in receipts
    )
    if actual_predecessor_fens != expected_predecessor_fens:
        raise RuntimeError(
            "V2 discovery receipt/FEN sequence or multiplicity mismatch"
        )

    audit = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "fresh_or_frozen_experiment_touched": False,
        "same_run_empty_start_r0": True,
        "training_only_discovery": True,
        "pool_manifest_sha256": pool_manifest["combined_sha256"],
        "discovery": {
            "r0_train_source_count": len(pools.r0_train),
            "gate_decoy_source_count": len(pools.gate_train_decoys),
            "combined_training_source_count": len(training_source_fens),
            "selected_count": len(ordered_fens),
            "training_source_fens_sha256": training_source_digest,
            "ordered_fens_sha256": _hash_json(ordered_fens),
            "receipt_count": len(receipts),
            "observed_outcome_counts": {
                "mate": sum(
                    receipt.observed_terminal_result for receipt in receipts
                ),
                "non_mate": sum(
                    not receipt.observed_terminal_result for receipt in receipts
                ),
            },
            "receipt_ids_sha256": _hash_json(
                tuple(receipt.event_id for receipt in receipts)
            ),
        },
        "candidate_count": len(frozen_candidates),
        "dormant_shadow_count": dormant_shadow_count,
        "initial_prospectively_certified_count": sum(
            state.prospectively_certified for state in authority.states.values()
        ),
        "structural_schedule": {
            "mode": authority.structural_mode.value,
            "opening_event_ordinal": int(source._next_event_ordinal),
            "prospective_events_before_structure": (
                None if adaptive else PROSPECTIVE_EVENTS_BEFORE_STRUCTURE
            ),
            "absolute_event_frontiers": (
                [] if adaptive else [absolute_structural_frontier]
            ),
            "frontier_policy": (
                "event_driven_at_quiescent_real_boundary"
                if adaptive else "single_predetermined_event_frontier"
            ),
        },
        "r0_persistent_state": dict(r0.persistent_state_audit()),
        "serialized_bytes": len(payload),
        "serialized_sha256": hashlib.sha256(payload).hexdigest(),
        "serialization_roundtrip_exact": True,
        "full_history_boundary_exact": True,
    }
    return authority, audit


def development_config(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_wall_seconds: float = 21_600.0,
    max_peak_rss_mib: float = 8_192.0,
) -> NativeIntrinsicCurriculumConfig:
    """Return the fixed one-shot PoC design; no learner knobs are exposed."""

    return NativeIntrinsicCurriculumConfig(
        output_path=str(output_dir / "result.json"),
        progress_path=str(output_dir / "progress.json"),
        seed=DEFAULT_SEED,
        r0_train_count=48,
        r0_validation_count=16,
        r0_regression_count=16,
        r0_gate_train_decoy_count=16,
        r0_gate_validation_decoy_count=16,
        r0_gate_regression_decoy_count=16,
        r1_train_count=48,
        r1_validation_count=16,
        r1_regression_count=16,
        r0_pool_mode="balanced_location",
        r0_excluded_fens=(),
        r1_pool_mode="balanced_setup",
        r0_epochs=96,
        r1_epochs=240,
        r0_replay_per_r1_epoch=0,
        r0_validation_interval=8,
        r1_validation_interval=20,
        r1_snapshot_interval=20,
        r1_snapshot_dir=str(output_dir / "snapshots"),
        resume_r1_snapshots=True,
        r1_keep_checkpoint_history=True,
        r0_availability_mode=V2_PROSPECTIVE_AVAILABILITY,
        run_redundant_child_ablation=False,
        max_samples=16,
        development_wall_ceiling_seconds=float(max_wall_seconds),
        development_peak_rss_ceiling_mib=float(max_peak_rss_mib),
        development_fen_fullmove_base=DEVELOPMENT_FEN_FULLMOVE_BASE,
    )


def run_development(
    config: NativeIntrinsicCurriculumConfig | None = None,
) -> NativeIntrinsicCurriculumResult:
    cfg = config or development_config()
    result = run_native_intrinsic_curriculum(
        config=cfg,
        r0_child_authority_factory=build_same_run_v2_r0_authority,
    )
    result.payload["development_protocol"] = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "single_predeclared_seed": int(cfg.seed),
        "new_deterministic_pool_is_permanently_viewed": True,
        "development_input_physical_identity_namespace": {
            "fullmove_base": DEVELOPMENT_FEN_FULLMOVE_BASE,
            "source_generators_emit_fullmove_number": 1,
            "purpose": (
                "exact FEN/physical-interaction separation from prior generated streams"
            ),
        },
        "frozen_experiment_touched": False,
        "learner_parameter_tuning_performed": False,
        "development_source_identity": _development_source_identity(),
        "fixed_work": {
            "r0": "48/16/16 balanced, cap 96 epochs",
            "r1": "48/16/16 balanced, full plus no-bootstrap, cap 240 epochs",
        },
        "resource_ceilings": {
            "wall_seconds_safe_epoch_boundary": cfg.development_wall_ceiling_seconds,
            "peak_rss_mib_safe_epoch_boundary": cfg.development_peak_rss_ceiling_mib,
        },
        "interpretation": "engineering_poc_only_no_r2_and_no_generalization_claim",
    }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-wall-seconds", type=float, default=21_600.0)
    parser.add_argument("--max-peak-rss-mib", type=float, default=8_192.0)
    args = parser.parse_args(argv)
    cfg = development_config(
        output_dir=args.output_dir,
        max_wall_seconds=args.max_wall_seconds,
        max_peak_rss_mib=args.max_peak_rss_mib,
    )
    started = perf_counter()
    attempt_path = args.output_dir / "attempt.json"
    try:
        result = run_development(cfg)
        output = Path(cfg.output_path)
        _atomic_write_json(output, result.to_dict())
    except R1DevelopmentCeilingReached as exc:
        _atomic_write_json(attempt_path, {
            "schema_version": SCHEMA_VERSION,
            "label": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "status": "CEILING_REACHED_AT_EXACT_EPOCH_SNAPSHOT",
            "epoch": exc.epoch,
            "snapshot_path": str(exc.snapshot_path),
            "reason": exc.reason,
            "wall_seconds": perf_counter() - started,
            "source_identity": _development_source_identity(),
            "config": asdict(cfg),
        })
        print(json.dumps({"status": "CEILING_REACHED", "attempt": str(attempt_path)}))
        return 2
    except Exception as exc:
        _atomic_write_json(attempt_path, {
            "schema_version": SCHEMA_VERSION,
            "label": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "wall_seconds": perf_counter() - started,
            "source_identity": _development_source_identity(),
            "config": asdict(cfg),
        })
        print(json.dumps({"status": "FAILED", "attempt": str(attempt_path)}))
        return 1
    _atomic_write_json(attempt_path, {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "status": "PASSED_TO_FIXED_WORK_COMPLETION",
        "result_path": str(output),
        "wall_seconds": perf_counter() - started,
        "source_identity": _development_source_identity(),
        "config": asdict(cfg),
    })
    print(json.dumps({"status": "PASSED", "result": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
