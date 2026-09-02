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
    AvailabilityState,
    CompetenceEnvelopeConfig,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from .native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    NativeIntrinsicCurriculumResult,
    R0_COMPETENCE_ID,
    R0DevelopmentCeilingReached,
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
# Certification is deliberately another content-defined slice of the same
# training-only source.  Keeping this count separate from the discovery
# constants makes the two ledgers (and their exclusion proof) explicit.
CERTIFICATION_TAPE_COUNT = 32
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


def _selection_identity_fen(fen: str) -> str:
    """Normalize a row for content-defined ranking when it is a FEN."""

    try:
        return chess.Board(str(fen)).fen()
    except (ValueError, TypeError):
        # A few unit-level callers use opaque stand-ins to test partition
        # ordering.  Production pool rows are all valid FENs; retaining the
        # stand-in keeps that compatibility path content-blind as well.
        return str(fen)


def _canonical_selection_fen(fen: str) -> str:
    """Return the canonical FEN used by content-defined row selection.

    Pool generation currently emits canonical FEN strings already, but the
    explicit normalization is part of the development protocol: selection
    must not depend on equivalent textual FEN spellings.  Keeping this helper
    local also means the discovery and certification audit can name the exact
    row identity that was used for the digest.
    """

    return _selection_identity_fen(fen)


def _selection_row_digest(fen: str) -> str:
    """Digest one canonical FEN for a stable, content-blind row identity."""

    canonical = _canonical_selection_fen(fen)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _neutral_certification_tape(
    source_fens: Sequence[str],
    discovery_fens: Sequence[str],
    *,
    count: int = CERTIFICATION_TAPE_COUNT,
) -> tuple[str, ...]:
    """Select a deterministic post-nomination tape from the same source.

    Rows are ranked only by a digest of canonical FEN, never by pool role,
    outcome, or generated input order.  Canonical de-duplication is important
    here: feeding two equivalent FEN spellings to the REAL authority would
    remint one physical interaction and correctly fail closed.  Returning the
    canonical FEN also makes the exclusion proof auditable by value.
    """

    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("certification tape count must be non-negative")
    discovery_canonical = {
        _canonical_selection_fen(fen) for fen in discovery_fens
    }
    candidates = {
        _canonical_selection_fen(fen)
        for fen in source_fens
    }.difference(discovery_canonical)
    ranked = sorted(
        candidates,
        key=lambda fen: (
            hashlib.sha256(
                b"native-intrinsic-v2-neutral-certification|"
                + fen.encode("utf-8")
            ).digest(),
            fen,
        ),
    )
    return tuple(ranked[:count])


def _certify_real_rows(
    authority: NativeProspectiveAuthorityV2,
    fens: Sequence[str],
) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    """Ground selected rows through the frozen authority's REAL capability.

    The only outcome read here is ``successor.is_checkmate()`` inside the
    authority-issued environment receipt.  No split labels, expected moves,
    or validation/regression rows enter this path.  One frozen frame session
    covers the complete tape so a shared R0 mutation would fail closed.
    """

    receipts: list[Any] = []
    emissions: list[Any] = []
    frame_session = authority.frame_session()
    try:
        for index, fen in enumerate(fens):
            predecessor = chess.Board(fen)
            frame = FrameContext(
                frame_id=f"native-intrinsic-v2-certification:{index:04d}",
                kind=FrameKind.REAL,
                values={"board": predecessor},
            )
            pending, trace = authority.open_real_event(
                frame,
                frame_session=frame_session,
            )
            if trace is None or trace.actuation is None:
                raise RuntimeError(
                    f"frozen R0 emitted no certification action at row {index}"
                )
            actuation = trace.actuation
            successor = predecessor.copy(stack=False)
            successor.push(chess.Move.from_uci(actuation.move_uci))
            receipt = authority.mint_environment_receipt(
                pending_token=pending.pending_token,
                trace=trace,
                predecessor=predecessor,
                successor=successor,
            )
            emission = authority.consume(
                receipt,
                frame_session=frame_session,
            )
            receipts.append(receipt)
            emissions.append(emission)
            if authority.structural_mode is StructuralMode.EVENT_DRIVEN:
                # REAL consumption is quiescent here.  Let the existing
                # content-blind authority safe point atomically settle the
                # complete bounded queue (including any contradiction-driven
                # recursive request) before the next row is admitted.
                authority.settle_pending_structural_requests()
    finally:
        frame_session.close()
    return tuple(receipts), tuple(emissions)


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
    certification_fens = _neutral_certification_tape(
        training_source_fens,
        ordered_fens,
    )
    discovery_canonical_fens = tuple(
        _canonical_selection_fen(fen) for fen in ordered_fens
    )
    certification_canonical_fens = tuple(
        _canonical_selection_fen(fen) for fen in certification_fens
    )
    source_canonical_fens = frozenset(
        _canonical_selection_fen(fen) for fen in training_source_fens
    )
    row_disjoint = not set(certification_canonical_fens).intersection(
        discovery_canonical_fens
    )
    partition_exact = bool(
        row_disjoint
        and set(discovery_canonical_fens).union(certification_canonical_fens)
        == source_canonical_fens
    )
    if len(training_source_fens) == 64 and not (
        len(ordered_fens) == DISCOVERY_TAPE_COUNT
        and len(certification_fens) == CERTIFICATION_TAPE_COUNT
        and partition_exact
    ):
        raise RuntimeError(
            "V2 production source must form an exact disjoint 32/32 partition"
        )
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
    discovery_payload = authority.dumps()
    discovery_restored = NativeProspectiveAuthorityV2.loads(discovery_payload)
    if discovery_restored.continuation_manifest() != authority.continuation_manifest():
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

    # Close nomination before exposing the held-out half of the same
    # training-only source.  Every certification row is then a prospective
    # REAL event; the frame session freezes the authority-owned R0 while the
    # environment derives the only outcome bit (checkmate at the successor).
    closure_boundary_start = len(authority.generation_boundaries)
    closure_consumption_count_start = len(authority.request_consumptions)
    closure_pending_count_start = len(authority._pending_request_ids())
    closure_consumption_start = frozenset(authority.request_consumptions)
    closure_generation_start = int(authority.current_generation)
    initial_prospectively_certified_count = sum(
        state.prospectively_certified for state in authority.states.values()
    )
    certification_receipts, certification_emissions = _certify_real_rows(
        authority,
        certification_fens,
    )
    discovery_receipt_ids = tuple(sorted(source.receipts))
    certification_receipt_ids = tuple(
        receipt.receipt_id for receipt in certification_receipts
    )
    discovery_physical_ids = frozenset(
        authority.discovery_prefix_physical_fingerprints
    )
    certification_physical_ids = frozenset(
        receipt.interaction_fingerprint
        for receipt in certification_receipts
    )
    certification_discovery_overlap = set(certification_receipt_ids).intersection(
        discovery_receipt_ids
    )
    physical_discovery_overlap = certification_physical_ids.intersection(
        discovery_physical_ids
    )
    if certification_discovery_overlap or physical_discovery_overlap:
        raise RuntimeError(
            "V2 certification reused discovery receipt or physical interaction"
        )
    if not row_disjoint:
        raise RuntimeError("V2 certification tape overlaps discovery tape")

    certification_ordinals = tuple(
        int(receipt.ordinal) for receipt in certification_receipts
    )
    candidate_birth_frontiers = tuple(
        int(state.hypothesis.birth_frontier)
        for state in authority.states.values()
    )
    certification_leak_rows = tuple(
        (state.hypothesis.cell_id, receipt_id)
        for state in authority.states.values()
        for receipt_id in state.certification_receipt_ids
        if authority.accepted_real_references[receipt_id].ordinal
        <= state.hypothesis.birth_frontier
    )
    all_certification_postbirth = not certification_leak_rows
    postbirth_frontier = (
        authority.next_expected_ordinal
        if certification_ordinals
        else max(candidate_birth_frontiers, default=-1) + 1
    )
    certified_available_count = sum(
        state.prospectively_certified
        and state.hypothesis.polarity is AvailabilityState.AVAILABLE
        for state in authority.states.values()
    )
    certified_refuted_count = sum(
        state.prospectively_certified
        and state.hypothesis.polarity is AvailabilityState.REFUTED
        for state in authority.states.values()
    )
    pending_structural_ids = tuple(
        authority._pending_request_ids()
        if callable(getattr(authority, "_pending_request_ids", None))
        else ()
    )
    closure_boundaries = tuple(
        authority.generation_boundaries[closure_boundary_start:]
    )
    closure_consumptions = tuple(
        authority.request_consumptions[request_id].manifest()
        for request_id in authority.request_consumptions
        if request_id not in closure_consumption_start
    )
    closure_generation_delta = (
        int(authority.current_generation) - closure_generation_start
    )
    closure_boundary_count_after = len(authority.generation_boundaries)
    closure_consumption_count_after = len(authority.request_consumptions)
    closure_pending_count_after = len(pending_structural_ids)
    if authority.structural_mode is StructuralMode.EVENT_DRIVEN and pending_structural_ids:
        raise RuntimeError(
            "event-driven V2 closure left structural requests pending"
        )
    # The development closure never arbitrarily picks one request from an
    # adaptive queue.  Event-driven requests are settled only by the
    # authority's existing content-blind safe point; scheduled requests remain
    # for their fixed predetermined frontier.
    structural_queue_audit = {
        "mode": authority.structural_mode.value,
        "pending_request_count": len(pending_structural_ids),
        "final_pending_request_count": len(pending_structural_ids),
        "pending_request_ids_sha256": _hash_json(pending_structural_ids),
        # In event-driven mode the safe point is invoked after every REAL
        # event, even when that event emitted no request.  Report both the
        # invocation contract and the number of non-empty batches so an empty
        # final queue cannot be mistaken for skipped closure.
        "safe_point_invocation_count": (
            len(certification_receipts)
            if authority.structural_mode is StructuralMode.EVENT_DRIVEN
            else 0
        ),
        "settled": (
            authority.structural_mode is StructuralMode.EVENT_DRIVEN
            or bool(closure_boundaries or closure_consumptions)
        ),
        "settled_request_batch_count": int(closure_generation_delta),
        "settled_request_count": len(closure_consumptions),
        "generation_delta": int(closure_generation_delta),
        "boundary_count": len(closure_boundaries),
        "consumption_count": len(closure_consumptions),
        "before": {
            "generation": int(closure_generation_start),
            "boundary_count": int(closure_boundary_start),
            "request_consumption_count": int(
                closure_consumption_count_start
            ),
            "pending_request_count": int(closure_pending_count_start),
        },
        "after": {
            "generation": int(authority.current_generation),
            "boundary_count": int(closure_boundary_count_after),
            "request_consumption_count": int(
                closure_consumption_count_after
            ),
            "pending_request_count": int(closure_pending_count_after),
        },
        "boundaries": [item.manifest() for item in closure_boundaries],
        "consumptions": list(closure_consumptions),
        "settlement_policy": (
            "per_real_event_content_blind_atomic_all_pending"
            if authority.structural_mode is StructuralMode.EVENT_DRIVEN
            else (
                "left_pending_for_predetermined_frontier"
                if pending_structural_ids else "no_requests_emitted"
            )
        ),
        "arbitrary_request_selection": False,
    }
    authority.verify_full_history_boundary(
        "native-intrinsic-v2-r0-competence-closure"
    )
    payload = authority.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    if restored.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError("same-run V2 closure failed exact roundtrip parity")
    restored.verify_full_history_boundary(
        "native-intrinsic-v2-r0-competence-closure-roundtrip"
    )

    audit = {
        "schema_version": SCHEMA_VERSION,
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "fresh_or_frozen_experiment_touched": False,
        "same_run_empty_start_r0": True,
        "training_only_discovery": True,
        "validation_regression_learning_excluded": True,
        "labels_or_move_oracle_used": False,
        "pool_manifest_sha256": pool_manifest["combined_sha256"],
        "discovery": {
            "r0_train_source_count": len(pools.r0_train),
            "gate_decoy_source_count": len(pools.gate_train_decoys),
            "combined_training_source_count": len(training_source_fens),
            "selected_count": len(ordered_fens),
            "training_source_fens_sha256": training_source_digest,
            "ordered_fens_sha256": _hash_json(ordered_fens),
            "canonical_fens_sha256": _hash_json(discovery_canonical_fens),
            "row_digests": [
                _selection_row_digest(fen) for fen in discovery_canonical_fens
            ],
            "row_digests_sha256": _hash_json(tuple(
                _selection_row_digest(fen) for fen in discovery_canonical_fens
            )),
            "receipt_ids": list(discovery_receipt_ids),
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
                discovery_receipt_ids
            ),
        },
        "certification": {
            "source": "r0_train_plus_gate_train_decoys",
            "source_count": len(training_source_fens),
            "selected_count": len(certification_fens),
            "canonical_fens_sha256": _hash_json(certification_canonical_fens),
            "ordered_fens_sha256": _hash_json(certification_fens),
            "row_digests": [
                _selection_row_digest(fen)
                for fen in certification_canonical_fens
            ],
            "row_digests_sha256": _hash_json(tuple(
                _selection_row_digest(fen)
                for fen in certification_canonical_fens
            )),
            "receipt_ids": list(certification_receipt_ids),
            "receipt_count": len(certification_receipts),
            "receipt_ids_sha256": _hash_json(certification_receipt_ids),
            "observed_outcome_counts": {
                "mate": sum(
                    receipt.observed_outcome
                    for receipt in certification_receipts
                ),
                "non_mate": sum(
                    not receipt.observed_outcome
                    for receipt in certification_receipts
                ),
            },
            "emission_count": len(certification_emissions),
            "environment_outcome_only": True,
            "labels_read": False,
            "move_oracle_used": False,
            "validation_rows_used": False,
            "regression_rows_used": False,
        },
        "row_partition": {
            "source_count": len(training_source_fens),
            "source_unique_canonical_count": len(source_canonical_fens),
            "discovery_count": len(discovery_canonical_fens),
            "certification_count": len(certification_canonical_fens),
            "discovery_certification_disjoint": row_disjoint,
            "exact_disjoint_partition": partition_exact,
            "source_canonical_fens_sha256": _hash_json(
                tuple(sorted(source_canonical_fens))
            ),
        },
        "receipt_disjointness": {
            "receipt_ids_disjoint": not certification_discovery_overlap,
            "physical_interactions_disjoint": not physical_discovery_overlap,
            "receipt_id_overlap_count": len(certification_discovery_overlap),
            "physical_interaction_overlap_count": len(physical_discovery_overlap),
            "all_certification_disjoint": not (
                certification_discovery_overlap or physical_discovery_overlap
            ),
        },
        "postbirth_frontier": postbirth_frontier,
        "postbirth_frontier_audit": {
            "first_certification_ordinal": (
                min(certification_ordinals, default=None)
            ),
            "last_certification_ordinal": (
                max(certification_ordinals, default=None)
            ),
            "next_expected_ordinal": int(authority.next_expected_ordinal),
            "candidate_birth_frontier_min": min(
                candidate_birth_frontiers, default=None
            ),
            "candidate_birth_frontier_max": max(
                candidate_birth_frontiers, default=None
            ),
            "certification_leak_count": len(certification_leak_rows),
            "all_certification_postbirth": all_certification_postbirth,
        },
        "certified_available_count": int(certified_available_count),
        "certified_refuted_count": int(certified_refuted_count),
        "certified_counts": {
            "available": int(certified_available_count),
            "refuted": int(certified_refuted_count),
            "total": int(
                certified_available_count + certified_refuted_count
            ),
        },
        "candidate_count": len(frozen_candidates),
        "dormant_shadow_count": dormant_shadow_count,
        "initial_prospectively_certified_count": int(
            initial_prospectively_certified_count
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
        "adaptive_structural_requests": structural_queue_audit,
        "r0_persistent_state": dict(r0.persistent_state_audit()),
        "serialized_bytes": len(payload),
        "serialized_sha256": hashlib.sha256(payload).hexdigest(),
        "serialization_roundtrip_exact": True,
        "full_history_boundary_exact": True,
        "discovery_roundtrip_serialized_bytes": len(discovery_payload),
        "discovery_roundtrip_exact": True,
    }
    return authority, audit


def build_empty_event_driven_v2_r0_authority(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    _pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
) -> tuple[NativeProspectiveAuthorityV2, Mapping[str, Any]]:
    """Wrap the trained R0 organism in an empty positive boundary shell.

    The adaptive ecology must discover competence boundaries from later REAL
    interaction.  It therefore starts with no discovery tape, no nominated
    positive or negative hypotheses, and no certification evidence.  The
    immutable R0 graph is still the native actuator/value substrate; the V2
    shell initially has no jurisdiction and can acquire it only through
    event-driven, post-birth positive certification.

    ``_pools`` is deliberately unread.  In particular, neither validation nor
    decoy membership can seed structure or decide which micropattern exists.
    """

    if config.r0_availability_mode != V2_PROSPECTIVE_AVAILABILITY:
        raise ValueError("empty V2 factory requires v2_prospective mode")
    if not config.r0_boundary_ecology_enabled:
        raise ValueError("empty V2 factory requires the boundary ecology")
    local_provider_ids = credit.direct_outcome_provider_ids(
        graph.triplet_ids
    )
    if not local_provider_ids:
        raise RuntimeError(
            "empty V2 factory requires a directly grounded local R0 provider"
        )
    local_provider_scope = frozenset(local_provider_ids)
    if graph.frozen_policy_triplet_ids != local_provider_scope:
        raise RuntimeError(
            "empty V2 factory requires the frozen R0 policy to equal its "
            "local direct-outcome provider set"
        )
    if graph.frozen_child_policy_token(local_provider_scope) is None:
        raise RuntimeError("empty V2 factory received an unbound R0 policy scope")

    graph_copy = copy.deepcopy(graph)
    credit_copy = copy.deepcopy(credit)
    r0 = NativeR0Organism(
        graph=graph_copy,
        credit=credit_copy,
        # The legacy singleton competence record remains only as a serialized
        # compatibility field.  In local-provider mode the organism never
        # consults it: each selected triplet must carry its own grounded REAL
        # outcome authority or the response abstains.
        provenance=FrozenCompetenceProvenance(
            child_id=R0_COMPETENCE_ID,
            mature=False,
            grounded=False,
            can_emit=False,
            consolidated_value=0.0,
            uncertainty=1.0,
            terminal_evidence=0,
            causal_confirmations=0,
            grounding_level=None,
            grounding_source="unused_in_local_direct_outcome_mode",
        ),
        # Keep the full graph as immutable archived substrate, but admit only
        # branches whose exact selected REAL returns earned local authority.
        # This prevents an exploratory nonprovider from winning first and
        # shadowing a valid mate-in-1 provider.
        frozen_triplet_ids=local_provider_scope,
        source_manifest={
            "kind": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "same_run_empty_start_r0": True,
            "curriculum_seed": int(config.seed),
            "boundary_initialization": "empty_event_driven_positive_shell",
            "pool_rows_read_for_boundary_initialization": 0,
            "validation_or_regression_rows_read": False,
            "local_direct_outcome_provider_count": len(
                local_provider_ids
            ),
            "authority_scope_triplet_count": len(local_provider_scope),
            "archived_graph_triplet_count": len(graph_copy.triplet_ids),
            "global_r0_competence_provider_used": False,
        },
    )
    envelope_seed = int(config.seed) ^ 0x56325052
    source = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=CompetenceEnvelopeConfig(
            selection_seed=envelope_seed
        ),
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=envelope_seed,
            completion_terminal_identity="mate",
            receipt_issuer_identity=(
                "native_intrinsic_v2_empty_boundary_adapter.v1"
            ),
            receipt_capability_key=(
                "native-intrinsic-v2-empty-boundary:"
                + hashlib.sha256(str(config.seed).encode("utf-8")).hexdigest()
            ),
        ),
    )
    authority = NativeProspectiveAuthorityV2.from_organism(
        source,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_epoch_schedule=(),
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    frozen_candidates = authority.close_nomination()

    zero_state = {
        "base_receipt_count": len(source.receipts),
        "base_cell_count": len(source.envelope.cells),
        "nominated_candidate_count": len(frozen_candidates),
        "authority_state_count": len(authority.states),
        "accepted_real_reference_count": len(
            authority.accepted_real_references
        ),
        "discovery_physical_fingerprint_count": len(
            authority.discovery_prefix_physical_fingerprints
        ),
        "boundary_promotion_request_count": len(
            authority.boundary_promotion_requests
        ),
        "pending_structural_request_count": len(
            authority._pending_request_ids()
        ),
    }
    if any(zero_state.values()):
        raise RuntimeError(
            "empty event-driven V2 authority acquired bootstrap evidence"
        )
    if authority.structural_epoch_schedule:
        raise RuntimeError("empty event-driven authority retained a schedule")
    if authority.structural_mode is not StructuralMode.EVENT_DRIVEN:
        raise RuntimeError("empty authority is not event-driven")

    authority.verify_full_history_boundary(
        "native-intrinsic-v2-empty-boundary"
    )
    payload = authority.dumps()
    restored = NativeProspectiveAuthorityV2.loads(payload)
    if restored.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError("empty V2 authority failed exact roundtrip parity")
    restored.verify_full_history_boundary(
        "native-intrinsic-v2-empty-boundary-roundtrip"
    )

    audit = {
        "schema_version": "native_intrinsic_v2_empty_boundary.v1",
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "fresh_or_frozen_experiment_touched": False,
        "same_run_empty_start_r0": True,
        "boundary_initialization": "empty_event_driven_positive_shell",
        "training_discovery_used": False,
        "training_certification_used": False,
        "validation_regression_learning_excluded": True,
        "labels_or_move_oracle_used": False,
        "pool_rows_read_for_boundary_initialization": 0,
        "positive_only_future_births": True,
        "negative_authority_roots_initialized": 0,
        "initial_state": zero_state,
        "candidate_count": 0,
        "local_direct_outcome_provider_count": len(local_provider_ids),
        "authority_scope_triplet_count": len(local_provider_scope),
        "archived_graph_triplet_count": len(graph_copy.triplet_ids),
        "nonprovider_archived_triplet_count": (
            len(graph_copy.triplet_ids) - len(local_provider_scope)
        ),
        "global_r0_competence_provider_used": False,
        "certified_available_count": 0,
        "certified_refuted_count": 0,
        "structural_mode": StructuralMode.EVENT_DRIVEN.value,
        "structural_epoch_schedule": [],
        "no_scheduled_frontiers": True,
        "structural_schedule": {
            "mode": StructuralMode.EVENT_DRIVEN.value,
            "absolute_event_frontiers": [],
            "scheduled_frontiers": [],
            "frontier_policy": "post_real_quiescent_atomic_all_pending",
            "no_scheduled_frontiers": True,
        },
        "serialization_roundtrip_exact": True,
        "full_history_boundary_exact": True,
        "serialized_bytes": len(payload),
        "serialized_sha256": hashlib.sha256(payload).hexdigest(),
        "continuation_digest": authority.continuation_digest(),
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
    except R0DevelopmentCeilingReached as exc:
        _atomic_write_json(attempt_path, {
            "schema_version": SCHEMA_VERSION,
            "label": DEVELOPMENT_LABEL,
            "scientific_use_permitted": False,
            "status": "R0_CEILING_REACHED_AT_COMPLETE_EPOCH_NON_RESUMABLE",
            "r0_pass": None,
            "r1_executed": None,
            "r1_pass": None,
            "work_completed": False,
            "curriculum_gate_passed": False,
            "mechanism_checks": {},
            "per_run_mechanism_gate_passed": False,
            "scientific_gate_passed": False,
            "multi_seed_scientific_adjudication_required": True,
            "resumable": False,
            "epoch": exc.epoch,
            "reason": exc.reason,
            "wall_seconds": perf_counter() - started,
            "source_identity": _development_source_identity(),
            "config": asdict(cfg),
        })
        print(json.dumps({"status": "R0_CEILING_REACHED", "attempt": str(attempt_path)}))
        return 2
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
