"""Additive initialization-order reclosure for deferred specialization.

The historical frozen discriminator, performance reclosure, and failed attempt
remain immutable.  This module changes one ordering edge only: the grown native
organism stays nomination-open while it is imported into V2, and the wrapper
then owns the single nomination close before candidate-identical arm cloning.
"""
from __future__ import annotations

import argparse
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from . import native_deferred_specialization_performance_reclosure as frozen
from .native_competence_envelope import (
    DormantOrigin,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    V2Mode,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


science = frozen.science

SCHEMA_VERSION = (
    "native_deferred_specialization_initialization_reclosure.v1"
)
MANIFEST_SCHEMA = (
    "native_deferred_specialization_initialization_reclosure_manifest.v1"
)
RESULT_SCHEMA = (
    "native_deferred_specialization_initialization_reclosure_result.v1"
)
CANARY_SCHEMA = (
    "native_deferred_specialization_initialization_canary.v1"
)
STARTING_COMMIT = "c1476253252248bfd981e6a66fb84f5671894cc3"
HISTORICAL_FRESH_RUNNER_SHA256 = (
    "35d83440b6060ef56f9908dc5b2fc82cb93e2241f364c40f97fea7f2f20ac9c3"
)
HISTORICAL_PERFORMANCE_RUNNER_SHA256 = (
    "fe8fdc182b501aedb0fc7341335b960b84a8746a3f1f618f4f23dde6765c44f2"
)
FAILED_ATTEMPT_SHA256 = (
    "01e241771e47c1094f81c30eca7007fbb820f0a269e8851c05feebea0ee02ccc"
)
VERIFIED_CACHE_SHA256 = (
    "2d364c274fab22863082daa09fc51d4e402df41c44ebb0d692539f0967c5403f"
)
FAILED_TERMINAL_RECORD_SHA256 = (
    "a2d790634f0523438edf23a1dc25e3de308942639e4fb9eddb22beaf5dc84b25"
)

SOURCE_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_deferred_specialization_initialization_reclosure.py"
)
TEST_PATH = Path(
    "tests/autogrowth/"
    "test_native_deferred_specialization_initialization_reclosure.py"
)
SOURCE_MANIFEST = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_initialization_reclosure_source_manifest.json"
)
RESULT_PLACEHOLDER = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_initialization_reclosure_result.json"
)
CANARY_PATH = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_initialization_canary.json"
)
FAILED_ATTEMPT_DIR = Path(
    "reports/autogrowth/runs/"
    "native_deferred_specialization_performance_attempt_v1"
)
FAILED_ATTEMPT_PATH = FAILED_ATTEMPT_DIR / "attempt.json"
VERIFIED_CACHE_PATH = FAILED_ATTEMPT_DIR / "r0_observation_cache.json"
FAILED_TERMINAL_RECORD = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_performance_attempt_v1_terminal_failure.json"
)
DEFAULT_ATTEMPT_DIR = Path(
    "reports/autogrowth/runs/"
    "native_deferred_specialization_initialization_reclosed_attempt_v1"
)
MAX_WORKERS = frozen.MAX_WORKERS

DEPENDENCY_PATHS = (
    SOURCE_PATH,
    TEST_PATH,
    frozen.SOURCE_PATH,
    science.SOURCE_PATH,
    Path("src/recon_lite_chess/autogrowth/native_competence_envelope.py"),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_trace_competence_authority.py"
    ),
)

_FROZEN_VERIFY_PERFORMANCE_MANIFEST = frozen._verify_performance_manifest


def _sha_json(value: Any) -> str:
    return frozen._sha_json(value)


def _sha_file(path: str | Path) -> str:
    return frozen._sha_file(path)


def _historical_hashes() -> dict[str, str]:
    return {
        str(science.SOURCE_PATH): _sha_file(science.SOURCE_PATH),
        str(frozen.SOURCE_PATH): _sha_file(frozen.SOURCE_PATH),
        str(FAILED_ATTEMPT_PATH): _sha_file(FAILED_ATTEMPT_PATH),
        str(VERIFIED_CACHE_PATH): _sha_file(VERIFIED_CACHE_PATH),
        str(FAILED_TERMINAL_RECORD): _sha_file(FAILED_TERMINAL_RECORD),
    }


def verify_historical_immutability() -> dict[str, str]:
    actual = _historical_hashes()
    expected = {
        str(science.SOURCE_PATH): HISTORICAL_FRESH_RUNNER_SHA256,
        str(frozen.SOURCE_PATH): HISTORICAL_PERFORMANCE_RUNNER_SHA256,
        str(FAILED_ATTEMPT_PATH): FAILED_ATTEMPT_SHA256,
        str(VERIFIED_CACHE_PATH): VERIFIED_CACHE_SHA256,
        str(FAILED_TERMINAL_RECORD): FAILED_TERMINAL_RECORD_SHA256,
    }
    if actual != expected:
        raise RuntimeError("historical frozen package or failed attempt drift")
    return actual


def _discovery_rows_only(
    rows: Sequence[science.StreamRow],
) -> tuple[science.StreamRow, ...]:
    selected = science.rows_by_region(rows, "parent_discovery")
    if (
        len(selected) != science.REGION_COUNTS["parent_discovery"]
        or any(row.region != "parent_discovery" for row in selected)
    ):
        raise RuntimeError("discovery-only row guard failed")
    return selected


def _grown_discovery_organism_cached(
    *,
    source: TraceNativeCompetenceOrganism,
    seed: int,
    discovery_rows: Sequence[science.StreamRow],
    cache: Mapping[str, frozen.CachedR0Observation],
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[TraceNativeCompetenceOrganism, tuple[Any, ...], tuple[Any, ...]]:
    if any(row.region != "parent_discovery" for row in discovery_rows):
        raise RuntimeError("non-discovery row supplied to initialization")
    envelope_config = replace(
        source.envelope.config, selection_seed=int(seed)
    )
    learning_config = replace(
        source.learning_config,
        genome_seed=int(seed),
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    organism = TraceNativeCompetenceOrganism.empty(
        source.r0,
        envelope_config=envelope_config,
        learning_config=learning_config,
    )
    organism.open_prospective_discovery_epoch()
    receipts = frozen._mint_discovery_receipts_cached(
        organism,
        discovery_rows,
        cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    organism.grow_from_grounded_receipts(
        receipts,
        finalize=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW,
    )
    epoch = organism.envelope.nomination_epoch
    if epoch is None or epoch.nomination_closed:
        raise RuntimeError("grown discovery organism is not nomination-open")
    shadow_parents = tuple(sorted(
        (
            cell for cell in organism.envelope.cells.values()
            if cell.state is StemCellState.DORMANT
            and cell.dormant_origin is DormantOrigin.MIXED_OUTCOME_SHADOW
            and cell.prune_reason == "mixed_outcomes"
            and cell.specialization_depth == 0
        ),
        key=lambda cell: (cell.born_request_ordinal, cell.cell_id),
    ))
    if not shadow_parents:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "fresh genome produced no mixed-outcome shadow parent",
        )
    return organism, tuple(receipts), shadow_parents


def _candidate_semantics(
    organism: TraceNativeCompetenceOrganism,
    cell_ids: Sequence[str],
) -> dict[str, Any]:
    result = {}
    for cell_id in sorted(cell_ids):
        cell = organism.envelope.cells[cell_id]
        escrow = cell.nomination_escrow
        result[cell_id] = {
            "members": list(cell.members),
            "polarity": None if cell.polarity is None else cell.polarity.value,
            "state": cell.state.name,
            "dormant_origin": (
                None if cell.dormant_origin is None
                else cell.dormant_origin.value
            ),
            "prune_reason": cell.prune_reason,
            "lineage_parent_id": cell.lineage_parent_id,
            "specialization_depth": cell.specialization_depth,
            "nomination_escrow": (
                None if escrow is None else escrow.manifest()
            ),
        }
    return result


def _receipt_ledger(
    organism: TraceNativeCompetenceOrganism,
) -> list[dict[str, Any]]:
    return [
        item.canonical_manifest()
        for item in sorted(
            organism.receipts.values(), key=lambda row: row.event_id
        )
    ]


def _evidence_ledger(
    organism: TraceNativeCompetenceOrganism,
) -> dict[str, Any]:
    return {
        key: asdict(value)
        for key, value in sorted(organism.envelope.evidence.items())
    }


def _candidate_arm_manifest(
    authority: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    epoch = authority.base.envelope.nomination_epoch
    if epoch is None or not epoch.nomination_closed:
        raise RuntimeError("candidate arm is not nomination-closed")
    return {
        "hypotheses": {
            key: state.hypothesis.manifest()
            for key, state in sorted(authority.states.items())
        },
        "escrows": {
            key: (
                None
                if authority.base.envelope.cells[key].nomination_escrow is None
                else authority.base.envelope.cells[
                    key
                ].nomination_escrow.manifest()
            )
            for key in sorted(authority.states)
        },
        "candidate_manifest": [
            list(item) for item in epoch.frozen_candidate_manifest
        ],
        "candidate_manifest_digest": epoch.frozen_candidate_manifest_digest,
        "authority_topology": copy.deepcopy(authority.authority_topology),
    }


def _clone_candidate_identical_arms_cached(
    *,
    source: TraceNativeCompetenceOrganism,
    seed: int,
    discovery_rows: Sequence[science.StreamRow],
    cache: Mapping[str, frozen.CachedR0Observation],
) -> tuple[
    dict[SpecializationMode, NativeProspectiveAuthorityV2],
    str,
    dict[str, Any],
]:
    source_r0_digest, source_continuation_digest = frozen._source_bindings(
        source
    )
    organism, _receipts, shadow_parents = _grown_discovery_organism_cached(
        source=source,
        seed=seed,
        discovery_rows=discovery_rows,
        cache=cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    parent = shadow_parents[0]
    template = NativeProspectiveAuthorityV2.from_organism(
        organism,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    template.close_nomination()
    template._verify_invariants()
    raw_arms = {
        mode: copy.deepcopy(template) for mode in science.ARMS
    }
    parity = {
        mode.value: _candidate_arm_manifest(authority)
        for mode, authority in raw_arms.items()
    }
    if len({_sha_json(value) for value in parity.values()}) != 1:
        raise RuntimeError("candidate-identical arms diverged before factor")
    for mode, authority in raw_arms.items():
        authority.specialization_mode = mode
        authority._verify_invariants()
    return raw_arms, parent.cell_id, {
        "candidate_identical_template_digest": template.continuation_digest(),
        "candidate_population_digest": _sha_json(
            next(iter(parity.values()))
        ),
        "parent_cell_id": parent.cell_id,
        "parent_manifest": parent.to_manifest(),
        "shadow_parent_count": len(shadow_parents),
    }


def prepare_seed_cached(
    *,
    ordinal: int,
    seed: int,
    source: TraceNativeCompetenceOrganism,
    stream: Sequence[science.StreamRow],
    cache: Mapping[str, frozen.CachedR0Observation],
) -> dict[str, Any]:
    source_r0_digest, source_continuation_digest = frozen._source_bindings(
        source
    )
    arms, parent_id, discovery = _clone_candidate_identical_arms_cached(
        source=source,
        seed=seed,
        discovery_rows=_discovery_rows_only(stream),
        cache=cache,
    )
    parent = frozen._parent_phase_cached(
        arms,
        parent_id,
        science.rows_by_region(
            stream, "parent_prospective_support_and_contradiction"
        ),
        cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    children, birth = science._birth_children(arms)
    exposure = frozen._scan_child_exposure_cached(
        arms,
        children,
        science.rows_by_region(stream, "child_prospective_certification"),
        cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    return {
        "ordinal": ordinal,
        "genome_seed": seed,
        "status": "PREPARED_BEFORE_POST_BIRTH_OUTCOMES",
        "source_r0_digest": source_r0_digest,
        "source_continuation_digest": source_continuation_digest,
        "discovery": discovery,
        "parent": parent,
        "birth": birth,
        "exposure": exposure,
        "authorities": arms,
    }


class _PrematureCloseCapture(NativeProspectiveAuthorityV2):
    captured: dict[str, Any] | None = None

    def _verify_invariants(
        self, *, allow_unregistered: bool = False
    ) -> None:
        try:
            super()._verify_invariants(
                allow_unregistered=allow_unregistered
            )
        except ProspectiveV2IntegrityError as exc:
            if str(exc) == "experimental initialization identity mismatch":
                expected = self._build_experimental_identity()
                type(self).captured = {
                    "actual_experimental_identity": copy.deepcopy(
                        self.experimental_identity
                    ),
                    "expected_experimental_identity": expected,
                }
            raise


def diagnose_seed_initialization(
    *,
    ordinal: int,
    seed: int,
    source: TraceNativeCompetenceOrganism,
    discovery_rows: Sequence[science.StreamRow],
    cache: Mapping[str, frozen.CachedR0Observation],
) -> dict[str, Any]:
    source_r0_digest, source_continuation_digest = frozen._source_bindings(
        source
    )
    organism, receipts, shadow_parents = _grown_discovery_organism_cached(
        source=source,
        seed=seed,
        discovery_rows=discovery_rows,
        cache=cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    open_epoch = organism.envelope.nomination_epoch
    assert open_epoch is not None
    parent = shadow_parents[0]
    reference = copy.deepcopy(organism)
    wrapper_source = copy.deepcopy(organism)
    premature = copy.deepcopy(organism)

    premature.close_prospective_nomination()
    _PrematureCloseCapture.captured = None
    premature_error = None
    try:
        _PrematureCloseCapture.from_organism(
            premature,
            mode=V2Mode.PROSPECTIVE,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        )
    except ProspectiveV2IntegrityError as exc:
        premature_error = str(exc)
    if (
        premature_error != "experimental initialization identity mismatch"
        or _PrematureCloseCapture.captured is None
    ):
        raise RuntimeError("premature-close path did not reproduce failure")

    reference_manifest = reference.close_prospective_nomination()
    reference_epoch = reference.envelope.nomination_epoch
    assert reference_epoch is not None
    wrapper = NativeProspectiveAuthorityV2.from_organism(
        wrapper_source,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    if (
        wrapper.base.envelope.nomination_epoch is None
        or wrapper.base.envelope.nomination_epoch.nomination_closed
        or wrapper.experimental_identity is not None
    ):
        raise RuntimeError("wrapper import did not preserve open nomination")
    wrapper_manifest = wrapper.close_nomination()
    wrapper._verify_invariants()
    wrapper_epoch = wrapper.base.envelope.nomination_epoch
    assert wrapper_epoch is not None
    expected_identity = wrapper._build_experimental_identity()
    captured = _PrematureCloseCapture.captured
    assert captured is not None
    if wrapper.experimental_identity != expected_identity:
        raise RuntimeError("wrapper initialization identity was not installed")

    candidate_ids = tuple(sorted(reference_epoch.post_epoch_cell_ids))
    reference_candidates = _candidate_semantics(reference, candidate_ids)
    wrapper_candidates = _candidate_semantics(wrapper.base, candidate_ids)
    if reference_candidates != wrapper_candidates:
        raise RuntimeError("reference/wrapper candidate semantics differ")
    if reference_manifest != wrapper_manifest:
        raise RuntimeError("reference/wrapper frozen manifest differs")
    if (
        reference_epoch.frozen_candidate_manifest_digest
        != wrapper_epoch.frozen_candidate_manifest_digest
    ):
        raise RuntimeError("reference/wrapper manifest digest differs")
    if _receipt_ledger(reference) != _receipt_ledger(wrapper.base):
        raise RuntimeError("reference/wrapper receipt ledger differs")
    if _evidence_ledger(reference) != _evidence_ledger(wrapper.base):
        raise RuntimeError("reference/wrapper evidence ledger differs")

    r0_reference = reference.r0.persistent_state_audit()
    r0_wrapper = wrapper.base.r0.persistent_state_audit()
    for key in frozen.R0_SEMANTIC_AUDIT_FIELDS:
        if r0_reference[key] != r0_wrapper[key]:
            raise RuntimeError(f"reference/wrapper R0 {key} differs")
    row = discovery_rows[0]
    board_a = chess.Board(row.predecessor_fen)
    board_b = chess.Board(row.predecessor_fen)
    actuation_a, trace_a = reference.r0.emit_action_with_trace(FrameContext(
        f"initialization-parity:{ordinal}",
        FrameKind.REAL,
        values={"board": board_a},
    ))
    actuation_b, trace_b = wrapper.base.r0.emit_action_with_trace(FrameContext(
        f"initialization-parity:{ordinal}",
        FrameKind.REAL,
        values={"board": board_b},
    ))
    if trace_a is None or trace_b is None:
        raise RuntimeError("R0 parity trace is absent")
    behavior_a = {
        "actuation": asdict(actuation_a),
        "trace": science._semantic_trace_manifest(trace_a),
        "successor": science._execute_transition(board_a, trace_a).fen(),
    }
    behavior_b = {
        "actuation": asdict(actuation_b),
        "trace": science._semantic_trace_manifest(trace_b),
        "successor": science._execute_transition(board_b, trace_b).fen(),
    }
    if behavior_a != behavior_b:
        raise RuntimeError("reference/wrapper emitted behavior differs")
    if (
        trace_a.source_organism_identity
        != trace_b.source_organism_identity
        or trace_a.source_state_identity != trace_b.source_state_identity
    ):
        raise RuntimeError("reference/wrapper source identities differ")

    raw_arms = {
        mode: copy.deepcopy(wrapper) for mode in science.ARMS
    }
    before_factor = {
        mode.value: _candidate_arm_manifest(authority)
        for mode, authority in raw_arms.items()
    }
    before_digests = {
        mode: _sha_json(value)
        for mode, value in before_factor.items()
    }
    if len(set(before_digests.values())) != 1:
        raise RuntimeError("pre-factor arm candidate parity failed")
    for mode, authority in raw_arms.items():
        authority.specialization_mode = mode
        authority._verify_invariants()
    topology_digests = {
        mode.value: _sha_json(authority.authority_topology)
        for mode, authority in raw_arms.items()
    }
    if len(set(topology_digests.values())) != 1:
        raise RuntimeError("post-factor decision topology parity failed")

    parent_manifest = parent.to_manifest()
    if (
        reference.envelope.cells[parent.cell_id].to_manifest()
        != parent_manifest
    ):
        raise RuntimeError("selected parent manifest changed")
    return {
        "ordinal": ordinal,
        "genome_seed": seed,
        "status": "INITIALIZATION_CANARY_PASSED",
        "discovery_rows_consumed": len(discovery_rows),
        "discovery_row_id_digest": _sha_json(
            [row.row_id for row in discovery_rows]
        ),
        "discovery_receipt_count": len(receipts),
        "nomination_closed_immediately_before_premature_from_organism": True,
        "nomination_closed_immediately_before_corrected_from_organism": False,
        "premature_error": premature_error,
        "premature_actual_experimental_identity": captured[
            "actual_experimental_identity"
        ],
        "premature_expected_initialization_identity_digest": captured[
            "expected_experimental_identity"
        ]["identity_digest"],
        "expected_initialization_identity_digest": expected_identity[
            "identity_digest"
        ],
        "corrected_experimental_identity_digest": wrapper.experimental_identity[
            "identity_digest"
        ],
        "experimental_identity_exact": (
            wrapper.experimental_identity == expected_identity
        ),
        "premature_corrected_identity_difference": (
            "the corrected identity includes the wrapper-owned "
            "NATIVE_NOMINATION_CLOSED event; the prematurely closed source "
            "cannot supply that event"
        ),
        "candidate_count": len(candidate_ids),
        "candidate_ids_digest": _sha_json(list(candidate_ids)),
        "candidate_semantics_digest": _sha_json(reference_candidates),
        "mixed_outcome_shadow_parent_count": len(shadow_parents),
        "selected_parent_id": parent.cell_id,
        "selected_parent_manifest": parent_manifest,
        "frozen_candidate_manifest": [list(item) for item in reference_manifest],
        "frozen_candidate_manifest_digest": (
            reference_epoch.frozen_candidate_manifest_digest
        ),
        "reference_wrapper_candidate_parity": True,
        "receipt_ledger_digest": _sha_json(_receipt_ledger(reference)),
        "evidence_ledger_digest": _sha_json(_evidence_ledger(reference)),
        "r0_component_digests": {
            key: r0_reference[key] for key in frozen.R0_SEMANTIC_AUDIT_FIELDS
        },
        "r0_emitted_behavior_digest": _sha_json(behavior_a),
        "source_organism_identity": trace_a.source_organism_identity,
        "source_state_identity": trace_a.source_state_identity,
        "arm_count": len(raw_arms),
        "pre_factor_arm_candidate_digests": before_digests,
        "post_factor_decision_topology_digests": topology_digests,
        "pre_parent_invariant_checks": len(raw_arms),
        "parent_prospective_events": 0,
        "exposure_scans": 0,
        "stage_b_events": 0,
        "unopened_outcome_events": 0,
        "byte_identity_exceptions": [
            "wrapper base cells add immutable_hypothesis_digest",
            "wrapper adds V2 states and structural invariants",
            "wrapper close adds experimental_identity, nomination event, and generation boundaries",
            "specialization_mode differs only after candidate-identical arm parity is recorded"
        ],
    }


def _canary_worker(ordinal: int, seed: int) -> dict[str, Any]:
    if frozen._WORKER_SOURCE is None:
        raise RuntimeError("canary worker source is not initialized")
    return diagnose_seed_initialization(
        ordinal=ordinal,
        seed=seed,
        source=frozen._WORKER_SOURCE,
        discovery_rows=_discovery_rows_only(frozen._WORKER_STREAM),
        cache=frozen._WORKER_CACHE,
    )


def run_initialization_canary(
    *, output: Path = CANARY_PATH, workers: int = MAX_WORKERS
) -> dict[str, Any]:
    if workers < 1 or workers > MAX_WORKERS:
        raise ValueError(f"workers must be in 1..{MAX_WORKERS}")
    verify_historical_immutability()
    _manifest, original, rows = _FROZEN_VERIFY_PERFORMANCE_MANIFEST()
    discovery_rows = _discovery_rows_only(rows)
    source_item = original["source_r0"]["source_item"]
    seeds = tuple(map(int, original["seed_derivation"]["genome_seeds"]))
    results = []
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=frozen._worker_initialize,
        initargs=(
            source_item,
            [row.manifest() for row in rows],
            str(VERIFIED_CACHE_PATH),
        ),
    ) as executor:
        futures = {
            executor.submit(_canary_worker, ordinal, seed): ordinal
            for ordinal, seed in enumerate(seeds)
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: int(item["ordinal"]))
    if [item["ordinal"] for item in results] != list(range(32)):
        raise RuntimeError("initialization canary seed set is incomplete")
    if any(
        item["status"] != "INITIALIZATION_CANARY_PASSED"
        or item["parent_prospective_events"] != 0
        or item["exposure_scans"] != 0
        or item["stage_b_events"] != 0
        or item["unopened_outcome_events"] != 0
        for item in results
    ):
        raise RuntimeError("initialization canary boundary was crossed")
    payload = {
        "schema_version": CANARY_SCHEMA,
        "status": "ENGINEERING_CANARY_COMPLETE",
        "scientific_claim": False,
        "source_commit": STARTING_COMMIT,
        "workers": workers,
        "cache_path": str(VERIFIED_CACHE_PATH),
        "cache_sha256": _sha_file(VERIFIED_CACHE_PATH),
        "cache_outcome_free": True,
        "discovery_region": "parent_discovery",
        "discovery_row_count": len(discovery_rows),
        "discovery_row_id_digest": _sha_json(
            [row.row_id for row in discovery_rows]
        ),
        "seed_count": len(results),
        "seed_pass_count": len(results),
        "wrapper_construction_count": len(results),
        "wrapper_closure_count": len(results),
        "experimental_identity_exact_count": sum(
            item["experimental_identity_exact"] for item in results
        ),
        "candidate_identical_arm_count": sum(
            item["arm_count"] for item in results
        ),
        "pre_parent_invariant_pass_count": sum(
            item["pre_parent_invariant_checks"] for item in results
        ),
        "parent_prospective_event_count": 0,
        "exposure_scan_count": 0,
        "stage_b_event_count": 0,
        "new_outcome_access_count": 0,
        "stopped_at": "IMMEDIATELY_BEFORE_FIRST_PARENT_PROSPECTIVE_ROW",
        "seeds": results,
    }
    payload["artifact_payload_sha256"] = _sha_json(payload)
    frozen._atomic_write_json(output, payload)
    return payload


def _run_shard(
    attempt_dir_text: str,
    attempt_id: str,
    stage: str,
    ordinal: int,
    seed: int,
    input_digest: str,
) -> dict[str, Any]:
    original = frozen.prepare_seed_cached
    frozen.prepare_seed_cached = prepare_seed_cached
    try:
        return frozen._run_shard(
            attempt_dir_text,
            attempt_id,
            stage,
            ordinal,
            seed,
            input_digest,
        )
    finally:
        frozen.prepare_seed_cached = original


def _run_stage_pool(
    executor: ProcessPoolExecutor,
    *,
    attempt_dir: Path,
    attempt_id: str,
    stage: str,
    seeds: Sequence[int],
    input_digest: str,
) -> None:
    futures = {}
    for ordinal, seed in enumerate(seeds):
        identity = frozen._shard_identity(
            attempt_id, stage, ordinal, int(seed), input_digest
        )
        state_path, _payload_path = frozen._shard_paths(
            attempt_dir, stage, ordinal
        )
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("shard_identity") != identity:
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    f"existing {stage} shard identity mismatch",
                )
            if state.get("state") == "COMPLETED":
                frozen._read_completed_shard(
                    attempt_dir, stage, ordinal, identity
                )
                continue
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"cannot resume {stage} shard {ordinal} from {state.get('state')}",
            )
        futures[
            executor.submit(
                _run_shard,
                str(attempt_dir),
                attempt_id,
                stage,
                ordinal,
                int(seed),
                input_digest,
            )
        ] = ordinal
    for future in as_completed(futures):
        future.result()


def prepare_source_manifest(
    *, output: Path = SOURCE_MANIFEST
) -> dict[str, Any]:
    historical = verify_historical_immutability()
    performance_manifest, original, rows = (
        _FROZEN_VERIFY_PERFORMANCE_MANIFEST()
    )
    if not CANARY_PATH.is_file():
        raise RuntimeError("initialization canary artifact is absent")
    canary = json.loads(CANARY_PATH.read_text(encoding="utf-8"))
    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "INITIALIZATION_RECLOSED_NOT_EXECUTED",
        "starting_commit": STARTING_COMMIT,
        "historical_byte_identity": historical,
        "failed_attempt_immutable": True,
        "sole_behavioral_correction": (
            "open -> grow -> V2 wrap -> wrapper close -> clone arms"
        ),
        "scientific_factor_changes": 0,
        "frozen_science_identity": {
            "genome_seeds": original["seed_derivation"]["genome_seeds"],
            "stream_sha256": original["stream_sha256"],
            "stream_row_count": len(rows),
            "stream_row_order": [row.row_id for row in rows],
            "arms": original["arms"],
            "frozen_rules": original["frozen_rules"],
            "preregistration": original["preregistration"],
            "source_r0": original["source_r0"],
        },
        "performance_manifest_payload_sha256": (
            performance_manifest["manifest_payload_sha256"]
        ),
        "initialization_canary": {
            "path": str(CANARY_PATH),
            "sha256": _sha_file(CANARY_PATH),
            "payload_sha256": canary["artifact_payload_sha256"],
            "seed_pass_count": canary["seed_pass_count"],
            "arm_pass_count": canary["candidate_identical_arm_count"],
            "new_outcome_access_count": canary["new_outcome_access_count"],
        },
        "source_hashes": {
            str(path): _sha_file(path) for path in DEPENDENCY_PATHS
        },
        "future_command": (
            "PYTHONPATH=src .venv/bin/python -m "
            "recon_lite_chess.autogrowth."
            "native_deferred_specialization_initialization_reclosure "
            "--execute-frozen-shards --attempt-dir "
            f"{DEFAULT_ATTEMPT_DIR} --workers {MAX_WORKERS}"
        ),
        "execution_authorized": False,
        "new_attempt_started": False,
        "parent_prospective_rows_accessed_by_reclosure": False,
        "exposure_rows_accessed_by_reclosure": False,
        "stage_b_rows_accessed_by_reclosure": False,
    }
    payload["manifest_payload_sha256"] = _sha_json(payload)
    frozen._atomic_write_json(output, payload)
    return payload


def prepare_result_placeholder(
    *, output: Path = RESULT_PLACEHOLDER
) -> dict[str, Any]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    payload = {
        "schema_version": RESULT_SCHEMA,
        "status": "INITIALIZATION_RECLOSED_NOT_EXECUTED",
        "source_manifest_path": str(SOURCE_MANIFEST),
        "source_manifest_sha256": _sha_file(SOURCE_MANIFEST),
        "source_manifest_payload_sha256": manifest[
            "manifest_payload_sha256"
        ],
        "failed_attempt_preserved": True,
        "scientific_execution_authorized": False,
        "scientific_execution_started": False,
        "scientific_result": None,
    }
    frozen._atomic_write_json(output, payload)
    return payload


def _verify_reclosure_manifest() -> tuple[
    dict[str, Any], dict[str, Any], tuple[science.StreamRow, ...]
]:
    verify_historical_immutability()
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected = manifest.pop("manifest_payload_sha256")
    if _sha_json(manifest) != expected:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "initialization reclosure manifest digest mismatch",
        )
    manifest["manifest_payload_sha256"] = expected
    for path, digest in manifest["source_hashes"].items():
        if _sha_file(path) != digest:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"initialization reclosure source drift: {path}",
            )
    performance_manifest, original, rows = (
        _FROZEN_VERIFY_PERFORMANCE_MANIFEST()
    )
    frozen_identity = manifest["frozen_science_identity"]
    if (
        frozen_identity["genome_seeds"]
        != original["seed_derivation"]["genome_seeds"]
        or frozen_identity["stream_sha256"] != original["stream_sha256"]
        or frozen_identity["stream_row_order"]
        != [row.row_id for row in rows]
        or frozen_identity["arms"] != original["arms"]
        or frozen_identity["frozen_rules"] != original["frozen_rules"]
        or manifest["performance_manifest_payload_sha256"]
        != performance_manifest["manifest_payload_sha256"]
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "initialization reclosure changed frozen science",
        )
    return manifest, original, rows


def execute_frozen_shards(
    *,
    attempt_dir: Path = DEFAULT_ATTEMPT_DIR,
    workers: int = MAX_WORKERS,
) -> dict[str, Any]:
    original_verify = frozen._verify_performance_manifest
    original_pool = frozen._run_stage_pool
    frozen._verify_performance_manifest = _verify_reclosure_manifest
    frozen._run_stage_pool = _run_stage_pool
    try:
        return frozen.execute_frozen_shards(
            attempt_dir=attempt_dir, workers=workers
        )
    finally:
        frozen._verify_performance_manifest = original_verify
        frozen._run_stage_pool = original_pool


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-initialization-canary", action="store_true")
    group.add_argument("--prepare-source-manifest", action="store_true")
    group.add_argument("--prepare-result-placeholder", action="store_true")
    group.add_argument("--execute-frozen-shards", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--attempt-dir", type=Path, default=DEFAULT_ATTEMPT_DIR)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    if args.run_initialization_canary:
        result = run_initialization_canary(
            output=args.output or CANARY_PATH, workers=args.workers
        )
    elif args.prepare_source_manifest:
        result = prepare_source_manifest(output=args.output or SOURCE_MANIFEST)
    elif args.prepare_result_placeholder:
        result = prepare_result_placeholder(
            output=args.output or RESULT_PLACEHOLDER
        )
    else:
        result = execute_frozen_shards(
            attempt_dir=args.attempt_dir, workers=args.workers
        )
    print(json.dumps({
        "status": result["status"] if "status" in result else result["state"],
        "output": str(args.output or (
            CANARY_PATH if args.run_initialization_canary
            else SOURCE_MANIFEST if args.prepare_source_manifest
            else RESULT_PLACEHOLDER if args.prepare_result_placeholder
            else args.attempt_dir
        )),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
