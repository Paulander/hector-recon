"""Performance-only reclosure for the frozen deferred-specialization science.

This module imports the frozen scientific definitions without changing them.
It adds only (1) an immutable outcome-free R0 trace cache and (2) restart-safe,
per-seed Stage-A/Stage-B shards.  Cache construction and shard execution are
reachable only through the explicit future execution command.
"""
from __future__ import annotations

import argparse
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
import os
from pathlib import Path
import pickle
import resource
import time
import traceback
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState

from . import native_deferred_specialization_fresh_discriminator as science
from . import native_prospective_evidence_authority_v2 as v2
from .native_authority_handover import (
    GraphActuation,
    GraphSignalTrace,
    GraphTerminalSignal,
)
from .native_competence_envelope import (
    AvailabilityState,
    DormantOrigin,
    MixedOutcomeDisposition,
    SpecializationMode,
)
from .native_prospective_evidence_authority_v2 import (
    GenerationPhase,
    NativeProspectiveAuthorityV2,
    PendingRealEvent,
    V2Mode,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SCHEMA_VERSION = "native_deferred_specialization_performance_reclosure.v1"
CACHE_SCHEMA = "native_deferred_specialization_r0_observation_cache.v1"
SHARD_STATE_SCHEMA = "native_deferred_specialization_shard_state.v1"
ATTEMPT_SCHEMA = "native_deferred_specialization_sharded_attempt.v1"
MANIFEST_SCHEMA = (
    "native_deferred_specialization_performance_source_manifest.v1"
)
RESULT_SCHEMA = (
    "native_deferred_specialization_performance_result.v1"
)
STARTING_COMMIT = "3d4fc8b08fecd7e68ca115b66c8f3fceaa3e5b5f"
ORIGINAL_SOURCE_MANIFEST_SHA256 = (
    "d8aa3011926803a18c3c0b5265ff4e1099aeec2cb161e044f93d624d21995531"
)
ORIGINAL_RESULT_PLACEHOLDER_SHA256 = (
    "4877e375745b0ca9c36e83d4ad27781f89b4be2ffe53baa32d86ff17bd2f96bd"
)
ORIGINAL_PROGRAM_SHA256 = (
    "35d83440b6060ef56f9908dc5b2fc82cb93e2241f364c40f97fea7f2f20ac9c3"
)
SOURCE_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_deferred_specialization_performance_reclosure.py"
)
TEST_PATH = Path(
    "tests/autogrowth/"
    "test_native_deferred_specialization_performance_reclosure.py"
)
PROFILE_PATH = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_performance_profile.json"
)
REPORT_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_DEFERRED_SPECIALIZATION_PERFORMANCE_RECLOSURE.md"
)
SOURCE_MANIFEST = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_performance_source_manifest.json"
)
RESULT_PLACEHOLDER = Path(
    "reports/autogrowth/native_authority/"
    "native_deferred_specialization_performance_result.json"
)
DEFAULT_ATTEMPT_DIR = Path(
    "reports/autogrowth/runs/"
    "native_deferred_specialization_performance_attempt_v1"
)
MAX_WORKERS = 8
FORBIDDEN_CACHE_KEYS = frozenset({
    "outcome", "actual_completion", "classification", "matching_cell_ids",
    "child", "child_id", "competence", "available_cell_ids",
    "refuted_cell_ids", "receipt", "pending_token",
})
R0_SEMANTIC_AUDIT_FIELDS = (
    "topology_sha256",
    "weights_sha256",
    "credit_sha256",
    "lifecycle_sha256",
)
DEPENDENCY_PATHS = (
    SOURCE_PATH,
    science.SOURCE_PATH,
    Path("src/recon_lite_chess/autogrowth/native_authority_handover.py"),
    Path("src/recon_lite_chess/autogrowth/native_competence_envelope.py"),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ),
    Path(
        "src/recon_lite_chess/autogrowth/"
        "native_trace_competence_authority.py"
    ),
    REPORT_PATH,
    TEST_PATH,
)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha_json(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: str | Path) -> str:
    return _sha_bytes(Path(path).read_bytes())


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_bytes(
        path,
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n",
    )


@dataclass(frozen=True)
class CachedR0Observation:
    schema_version: str
    row_id: str
    predecessor_fen: str
    frame_id: str
    source_r0_persistent_digest: str
    source_r0_component_digests: dict[str, str]
    source_organism_continuation_digest: str
    source_organism_identity: str
    source_state_identity: str
    actuation: dict[str, Any]
    ordered_signal_identities: tuple[str, ...]
    terminal_source_identities: tuple[str, ...]
    terminal_signals: tuple[dict[str, Any], ...]
    semantic_trace_digest: str
    trace_manifest: dict[str, Any]
    successor_fen: str
    record_digest: str

    def unsigned_manifest(self) -> dict[str, Any]:
        result = asdict(self)
        result.pop("record_digest")
        return result

    def manifest(self) -> dict[str, Any]:
        return asdict(self)

    def trace(self) -> GraphSignalTrace:
        manifest = self.trace_manifest
        return GraphSignalTrace(
            frame_id=str(manifest["frame_id"]),
            frame_kind=str(manifest["frame_kind"]),
            source_organism_identity=str(manifest["source_organism_identity"]),
            source_state_identity=str(manifest["source_state_identity"]),
            option_identity=str(manifest["option_identity"]),
            actuation=GraphActuation(**manifest["actuation"]),
            confirmed_base_terminal_node_ids=tuple(
                map(str, manifest["confirmed_base_terminal_node_ids"])
            ),
            confirmed_mature_composite_ids=tuple(
                map(str, manifest["confirmed_mature_composite_ids"])
            ),
            terminal_signals=tuple(
                GraphTerminalSignal(**item)
                for item in manifest["terminal_signals"]
            ),
        )

    @classmethod
    def from_manifest(cls, payload: Mapping[str, Any]) -> "CachedR0Observation":
        return cls(
            **{
                **dict(payload),
                "ordered_signal_identities": tuple(
                    payload["ordered_signal_identities"]
                ),
                "terminal_source_identities": tuple(
                    payload["terminal_source_identities"]
                ),
                "terminal_signals": tuple(payload["terminal_signals"]),
            }
        )


def _r0_component_digests(
    source: TraceNativeCompetenceOrganism,
) -> dict[str, str]:
    audit = source.r0.persistent_state_audit()
    return {key: str(audit[key]) for key in R0_SEMANTIC_AUDIT_FIELDS}


def _source_bindings(source: TraceNativeCompetenceOrganism) -> tuple[str, str]:
    components = _r0_component_digests(source)
    return (
        _sha_json(components),
        _sha_json(source.continuation_manifest_v3()),
    )


def _validate_cache_record(
    record: CachedR0Observation,
    *, source_r0_digest: str,
    source_continuation_digest: str,
    row: science.StreamRow,
) -> GraphSignalTrace:
    if FORBIDDEN_CACHE_KEYS.intersection(record.manifest()):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "R0 cache contains outcome, competence, pending, or child data",
        )
    if (
        record.schema_version != CACHE_SCHEMA
        or record.row_id != row.row_id
        or record.predecessor_fen != row.predecessor_fen
        or record.source_r0_persistent_digest != source_r0_digest
        or not _valid_r0_component_binding(source_r0_digest, record)
        or record.source_organism_continuation_digest
        != source_continuation_digest
        or _sha_json(record.unsigned_manifest()) != record.record_digest
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"cached R0 binding mismatch for {row.row_id}",
        )
    trace = record.trace()
    if (
        trace.frame_kind != FrameKind.REAL.name
        or asdict(trace.actuation) != record.actuation
        or trace.ordered_signal_identities != record.ordered_signal_identities
        or tuple(
            signal.source_node_identity for signal in trace.terminal_signals
        ) != record.terminal_source_identities
        or tuple(asdict(item) for item in trace.terminal_signals)
        != record.terminal_signals
        or trace.source_organism_identity != record.source_organism_identity
        or trace.source_state_identity != record.source_state_identity
        or science._trace_digest(trace) != record.semantic_trace_digest
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"cached R0 semantic mismatch for {row.row_id}",
        )
    board = chess.Board(row.predecessor_fen)
    if science._execute_transition(board, trace).fen() != record.successor_fen:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"cached successor mismatch for {row.row_id}",
        )
    return trace


def _valid_r0_component_binding(
    expected_digest: str,
    record: CachedR0Observation,
) -> bool:
    components = record.source_r0_component_digests
    return (
        set(components) == set(R0_SEMANTIC_AUDIT_FIELDS)
        and _sha_json(components) == expected_digest
    )


def build_observation_cache(
    source: TraceNativeCompetenceOrganism,
    rows: Sequence[science.StreamRow],
    *,
    frame_namespace: str,
) -> tuple[CachedR0Observation, ...]:
    """Build an outcome-free trace cache; callers control row provenance."""

    source_r0_digest, source_continuation_digest = _source_bindings(source)
    source_r0_components = _r0_component_digests(source)
    result = []
    for row in rows:
        frame_id = f"{frame_namespace}:{row.row_id}"
        board = chess.Board(row.predecessor_fen)
        actuation, trace = source.r0.emit_action_with_trace(FrameContext(
            frame_id, FrameKind.REAL, values={"board": board}
        ))
        if actuation is None or trace is None:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"R0 emitted no cached observation for {row.row_id}",
            )
        unsigned = {
            "schema_version": CACHE_SCHEMA,
            "row_id": row.row_id,
            "predecessor_fen": row.predecessor_fen,
            "frame_id": frame_id,
            "source_r0_persistent_digest": source_r0_digest,
            "source_r0_component_digests": source_r0_components,
            "source_organism_continuation_digest": source_continuation_digest,
            "source_organism_identity": trace.source_organism_identity,
            "source_state_identity": trace.source_state_identity,
            "actuation": asdict(actuation),
            "ordered_signal_identities": tuple(
                trace.ordered_signal_identities
            ),
            "terminal_source_identities": tuple(
                signal.source_node_identity
                for signal in trace.terminal_signals
            ),
            "terminal_signals": tuple(
                asdict(item) for item in trace.terminal_signals
            ),
            "semantic_trace_digest": science._trace_digest(trace),
            "trace_manifest": trace.canonical_manifest(),
            "successor_fen": science._execute_transition(board, trace).fen(),
        }
        result.append(CachedR0Observation(
            **unsigned, record_digest=_sha_json(unsigned)
        ))
    return tuple(result)


def cache_payload(
    source: TraceNativeCompetenceOrganism,
    rows: Sequence[science.StreamRow],
    observations: Sequence[CachedR0Observation],
) -> dict[str, Any]:
    source_r0_digest, source_continuation_digest = _source_bindings(source)
    payload = {
        "schema_version": CACHE_SCHEMA,
        "source_r0_persistent_digest": source_r0_digest,
        "source_r0_component_digests": _r0_component_digests(source),
        "source_organism_continuation_digest": source_continuation_digest,
        "row_count": len(rows),
        "row_order": [row.row_id for row in rows],
        "records": [item.manifest() for item in observations],
        "contains_outcomes": False,
        "contains_competence_or_matching": False,
    }
    payload["payload_digest"] = _sha_json(payload)
    return payload


def load_and_verify_cache(
    path: Path,
    source: TraceNativeCompetenceOrganism,
    rows: Sequence[science.StreamRow],
) -> dict[str, CachedR0Observation]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.pop("payload_digest")
    if _sha_json(payload) != expected:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP, "cache payload digest mismatch"
        )
    source_r0_digest, source_continuation_digest = _source_bindings(source)
    observations = tuple(
        CachedR0Observation.from_manifest(item) for item in payload["records"]
    )
    if (
        payload["schema_version"] != CACHE_SCHEMA
        or payload["row_order"] != [row.row_id for row in rows]
        or payload["row_count"] != len(rows)
        or len(observations) != len(rows)
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP, "cache row identity mismatch"
        )
    for row, record in zip(rows, observations):
        _validate_cache_record(
            record,
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
            row=row,
        )
    return {item.row_id: item for item in observations}


def open_cached_real_event(
    authority: NativeProspectiveAuthorityV2,
    row: science.StreamRow,
    record: CachedR0Observation,
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[PendingRealEvent, GraphSignalTrace]:
    """Open one organism-owned event using only a bound immutable R0 trace."""

    authority._verify_invariants()
    if authority.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
        raise v2.ProspectiveV2IntegrityError(
            "REAL event outside PROSPECTIVE_OPEN"
        )
    if authority.evaluation_sealed or authority.pending_event is not None:
        raise v2.ProspectiveV2IntegrityError(
            "cached REAL event requires idle unsealed authority"
        )
    epoch = authority.base.envelope.nomination_epoch
    if epoch is None or not epoch.nomination_closed:
        raise v2.ProspectiveV2IntegrityError(
            "first certification event requires closed nomination"
        )
    if _sha_json(_r0_component_digests(authority.base)) != source_r0_digest:
        raise v2.ProspectiveV2IntegrityError(
            "cached observation R0 differs from organism R0"
        )
    before = authority.continuation_digest()
    trace = _validate_cache_record(
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
        row=row,
    )
    graph = authority._graph_measure(trace)
    matching = graph["commitment"]
    classification = authority._classification_from_emissions(
        authority.states, graph
    )
    typed_digest = v2._sha([asdict(item) for item in trace.terminal_signals])
    structure_digest = authority._structure_invariant_digest()
    token = v2._sha({
        "implementation": v2.IMPLEMENTATION_IDENTITY,
        "ordinal": authority.next_expected_ordinal,
        "frame_id": record.frame_id,
        "trace": trace.digest(),
        "matching": list(matching),
        "structure_invariant_digest": structure_digest,
    })
    pending = PendingRealEvent(
        ordinal=authority.next_expected_ordinal,
        frame_id=record.frame_id,
        trace_digest=trace.digest(),
        typed_signal_digest=typed_digest,
        source_organism_identity=trace.source_organism_identity,
        source_state_identity=trace.source_state_identity,
        predecessor_fen=row.predecessor_fen,
        actuation=trace.actuation,
        pre_outcome_classification=classification,
        matching_cell_ids=matching,
        matching_cell_digest=v2._sha(list(matching)),
        structure_invariant_digest=structure_digest,
        pending_token=token,
        outcome_terminal_identity=v2.OUTCOME_TERMINAL_IDENTITY,
        environment_outcome_terminal_identity=(
            authority.base.learning_config.completion_terminal_identity
        ),
    )
    if authority.continuation_digest() != before:
        raise v2.ProspectiveV2IntegrityError(
            "cached prediction mutated persistent state"
        )
    authority.pending_event = pending
    authority.event_transactions[token] = pending.manifest()
    return pending, trace


def evaluate_cached_observation(
    authority: NativeProspectiveAuthorityV2,
    row: science.StreamRow,
    record: CachedR0Observation,
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> dict[str, Any]:
    if not authority.evaluation_sealed:
        raise v2.ProspectiveV2IntegrityError(
            "cached evaluation requires sealed authority"
        )
    before = authority.continuation_digest()
    trace = _validate_cache_record(
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
        row=row,
    )
    graph = authority._graph_measure(trace)
    classification = authority._classification_from_emissions(
        authority.states, graph
    )
    if authority.continuation_digest() != before:
        raise v2.ProspectiveV2IntegrityError(
            "cached sealed evaluation mutated authority"
        )
    return {"trace": trace, "classification": classification, "graph": graph}


def _mint_discovery_receipts_cached(
    organism: TraceNativeCompetenceOrganism,
    rows: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[Any, ...]:
    terminal = organism.completion_terminal()
    receipts = []
    for row in rows:
        record = cache[row.row_id]
        trace = _validate_cache_record(
            record,
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
            row=row,
        )
        board = chess.Board(row.predecessor_fen)
        receipts.append(terminal.mint(
            trace, board, science._execute_transition(board, trace)
        ))
    return tuple(receipts)


def _clone_candidate_identical_arms_cached(
    *,
    source: TraceNativeCompetenceOrganism,
    seed: int,
    discovery_rows: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[dict[SpecializationMode, NativeProspectiveAuthorityV2], str, dict[str, Any]]:
    envelope_config = replace(source.envelope.config, selection_seed=int(seed))
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
    receipts = _mint_discovery_receipts_cached(
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
    organism.close_prospective_nomination()
    shadow_parents = sorted(
        (
            cell for cell in organism.envelope.cells.values()
            if cell.state is StemCellState.DORMANT
            and cell.dormant_origin is DormantOrigin.MIXED_OUTCOME_SHADOW
            and cell.prune_reason == "mixed_outcomes"
            and cell.specialization_depth == 0
        ),
        key=lambda cell: (cell.born_request_ordinal, cell.cell_id),
    )
    if not shadow_parents:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "fresh genome produced no mixed-outcome shadow parent",
        )
    parent = shadow_parents[0]
    template = NativeProspectiveAuthorityV2.from_organism(
        organism,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    template.close_nomination()
    arms = {mode: copy.deepcopy(template) for mode in science.ARMS}
    for mode, authority in arms.items():
        authority.specialization_mode = mode
    return arms, parent.cell_id, {
        "candidate_identical_template_digest": template.continuation_digest(),
        "parent_cell_id": parent.cell_id,
        "parent_manifest": parent.to_manifest(),
        "shadow_parent_count": len(shadow_parents),
    }


def _open_all_cached(
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    row: science.StreamRow,
    cache: Mapping[str, CachedR0Observation],
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[dict[SpecializationMode, Any], dict[SpecializationMode, GraphSignalTrace]]:
    pending = {}
    traces = {}
    for mode, authority in arms.items():
        pending[mode], traces[mode] = open_cached_real_event(
            authority,
            row,
            cache[row.row_id],
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
        )
    semantic = [science._semantic_trace_manifest(traces[mode]) for mode in science.ARMS]
    if semantic[1:] != semantic[:-1]:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"cached arm semantic divergence at {row.row_id}",
        )
    return pending, traces


def _parent_phase_cached(
    arms: dict[SpecializationMode, NativeProspectiveAuthorityV2],
    parent_id: str,
    rows: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> dict[str, Any]:
    parent_certified = False
    ledger = []
    for row in rows:
        pending, traces = _open_all_cached(
            arms,
            row,
            cache,
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
        )
        states = [
            pending[mode].pre_outcome_classification.to_manifest()
            for mode in science.ARMS
        ]
        matches = [pending[mode].matching_cell_ids for mode in science.ARMS]
        if states[1:] != states[:-1] or matches[1:] != matches[:-1]:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached arms diverged before parent outcome",
            )
        before = science.preoutcome_record(
            row=row,
            classification=pending[science.ARMS[0]].pre_outcome_classification,
            matching_cell_ids=pending[science.ARMS[0]].matching_cell_ids,
            selected_action=traces[science.ARMS[0]].actuation.move_uci,
        )
        emissions = science._consume_all_arms(arms, row, pending, traces)
        certification_states = [
            arms[mode].states[parent_id].prospectively_certified
            for mode in science.ARMS
        ]
        if certification_states[1:] != certification_states[:-1]:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached parent lifecycle diverged before arm factor",
            )
        parent_certified = parent_certified or certification_states[0]
        graph_revocations = [
            tuple(emissions[mode].graph_revocation_ids)
            for mode in science.ARMS
        ]
        ledger.append({
            **before,
            "outcome_committed": True,
            "observed_outcome": science._execute_transition(
                chess.Board(row.predecessor_fen), traces[science.ARMS[0]]
            ).is_checkmate(),
            "parent_certified_after": certification_states[0],
            "prequential_false_authority_ids": list(
                emissions[science.ARMS[0]].prequential_false_authority_ids
            ),
            "graph_revocation_ids": list(graph_revocations[0]),
        })
        if parent_id in graph_revocations[0]:
            if not parent_certified:
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    "cached parent revocation occurred without certification",
                )
            if any(parent_id not in ids for ids in graph_revocations):
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    "cached parent revocation diverged across arms",
                )
            break
    else:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "cached parent region did not certify and contradict",
        )
    local_requests = tuple(
        arms[SpecializationMode.LOCAL_CONTRAST].deferred_requests.values()
    )
    blind_requests = tuple(
        arms[SpecializationMode.COUNTEREXAMPLE_BLIND].deferred_requests.values()
    )
    disconnected_requests = tuple(
        arms[SpecializationMode.DISCONNECTED].deferred_requests.values()
    )
    if (
        len(local_requests) != 1
        or len(blind_requests) != 1
        or disconnected_requests
        or local_requests[0].parent_cell_id != parent_id
        or blind_requests[0].parent_cell_id != parent_id
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "cached parent contradiction did not create exact requests",
        )
    local = local_requests[0]
    blind = blind_requests[0]
    if (
        science._anonymous_candidate_population(local)
        != science._anonymous_candidate_population(blind)
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "local/blind request budget or candidate population diverged",
        )
    return {
        "rows_consumed": len(ledger),
        "ledger": ledger,
        "local_request_id": local.request_id,
        "blind_request_id": blind.request_id,
        "candidate_terminal_population_sha256": _sha_json(
            science._anonymous_candidate_population(local)
        ),
        "candidate_terminal_count": len(local.candidate_terminals),
    }


def _scan_child_exposure_cached(
    arms: Mapping[SpecializationMode, NativeProspectiveAuthorityV2],
    child_ids: Mapping[SpecializationMode, str],
    rows: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> dict[str, int]:
    counts = {mode: 0 for mode in science.SPECIALIZATION_ARMS}
    before = {mode: item.continuation_digest() for mode, item in arms.items()}
    for row in rows:
        traces = []
        for mode, authority in arms.items():
            trace = _validate_cache_record(
                cache[row.row_id],
                source_r0_digest=source_r0_digest,
                source_continuation_digest=source_continuation_digest,
                row=row,
            )
            graph = authority._graph_measure(trace)
            authority._classification_from_emissions(authority.states, graph)
            traces.append(science._semantic_trace_manifest(trace))
            if (
                mode in science.SPECIALIZATION_ARMS
                and child_ids[mode] in graph["commitment"]
            ):
                counts[mode] += 1
        if traces[1:] != traces[:-1]:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached exposure semantic divergence",
            )
    if any(
        authority.continuation_digest() != before[mode]
        for mode, authority in arms.items()
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "cached exposure scan mutated organism",
        )
    return {
        "local_count": counts[SpecializationMode.LOCAL_CONTRAST],
        "blind_count": counts[SpecializationMode.COUNTEREXAMPLE_BLIND],
    }


def prepare_seed_cached(
    *,
    ordinal: int,
    seed: int,
    source: TraceNativeCompetenceOrganism,
    stream: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
) -> dict[str, Any]:
    source_r0_digest, source_continuation_digest = _source_bindings(source)
    arms, parent_id, discovery = _clone_candidate_identical_arms_cached(
        source=source,
        seed=seed,
        discovery_rows=science.rows_by_region(stream, "parent_discovery"),
        cache=cache,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    parent = _parent_phase_cached(
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
    exposure = _scan_child_exposure_cached(
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
        "discovery": discovery,
        "parent_phase": parent,
        "child_birth": birth,
        "child_ids": {mode.value: value for mode, value in children.items()},
        "exposure": {"ordinal": ordinal, **exposure},
        "authorities": arms,
        "r0_source_state": source.r0.persistent_state_audit(),
    }


def certify_and_evaluate_seed_cached(
    prepared: Mapping[str, Any],
    certification_rows: Sequence[science.StreamRow],
    evaluation_rows: Sequence[science.StreamRow],
    cache: Mapping[str, CachedR0Observation],
    *,
    source_r0_digest: str,
    source_continuation_digest: str,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    arms = prepared["authorities"]
    child_ids = {
        SpecializationMode(key): value
        for key, value in prepared["child_ids"].items()
    }
    ledgers = {mode.value: [] for mode in science.ARMS}
    child_false = {mode.value: [] for mode in science.SPECIALIZATION_ARMS}
    child_revocations = {
        mode.value: [] for mode in science.SPECIALIZATION_ARMS
    }
    revoked = {mode: False for mode in science.SPECIALIZATION_ARMS}
    for row in certification_rows:
        pending, traces = _open_all_cached(
            arms,
            row,
            cache,
            source_r0_digest=source_r0_digest,
            source_continuation_digest=source_continuation_digest,
        )
        committed = {
            mode: science.preoutcome_record(
                row=row,
                classification=pending[mode].pre_outcome_classification,
                matching_cell_ids=pending[mode].matching_cell_ids,
                selected_action=traces[mode].actuation.move_uci,
            ) for mode in science.ARMS
        }
        for mode in science.SPECIALIZATION_ARMS:
            child_id = child_ids[mode]
            if revoked[mode] and child_id in {
                *pending[mode].pre_outcome_classification.available_cell_ids,
                *pending[mode].pre_outcome_classification.refuted_cell_ids,
            }:
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    "revoked child retained cached post-revocation influence",
                )
        emissions = science._consume_all_arms(arms, row, pending, traces)
        actual = science._execute_transition(
            chess.Board(row.predecessor_fen), traces[science.ARMS[0]]
        ).is_checkmate()
        for mode in science.ARMS:
            emission = emissions[mode]
            ledgers[mode.value].append({
                **committed[mode],
                "outcome_committed": True,
                "observed_outcome": actual,
                "prequential_false_authority_ids": list(
                    emission.prequential_false_authority_ids
                ),
                "graph_maturity_ids": list(emission.graph_maturity_ids),
                "graph_revocation_ids": list(emission.graph_revocation_ids),
                "graph_specialization_request_ids": list(
                    emission.graph_specialization_request_ids
                ),
            })
            if mode in science.SPECIALIZATION_ARMS:
                child_id = child_ids[mode]
                if child_id in emission.prequential_false_authority_ids:
                    child_false[mode.value].append(row.row_id)
                if child_id in emission.graph_revocation_ids:
                    child_revocations[mode.value].append(row.row_id)
                    revoked[mode] = True
    arm_results = {}
    frozen_payloads = {}
    for mode, authority in arms.items():
        live_manifest = authority.continuation_manifest()
        restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
        if restored.continuation_manifest() != live_manifest:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached post-certification roundtrip mismatch",
            )
        restored.seal_read_only_evaluation()
        frozen_manifest = restored.continuation_manifest()
        decisions = []
        for row in evaluation_rows:
            opened = evaluate_cached_observation(
                restored,
                row,
                cache[row.row_id],
                source_r0_digest=source_r0_digest,
                source_continuation_digest=source_continuation_digest,
            )
            trace = opened["trace"]
            classification = opened["classification"]
            successor = science._execute_transition(
                chess.Board(row.predecessor_fen), trace
            )
            decisions.append({
                "row_id": row.row_id,
                "available": (
                    classification.state is AvailabilityState.AVAILABLE
                ),
                "actual": successor.is_checkmate(),
                "available_cell_ids": list(classification.available_cell_ids),
                "refuted_cell_ids": list(classification.refuted_cell_ids),
                "semantic_trace_digest": science._trace_digest(trace),
            })
        if restored.continuation_manifest() != frozen_manifest:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached sealed evaluation changed manifest",
            )
        if restored.base.r0.persistent_state_audit() != prepared["r0_source_state"]:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "cached path changed R0 persistent state",
            )
        frozen_payloads[mode.value] = restored.dumps()
        arm_results[mode.value] = {
            "certification_ledger": ledgers[mode.value],
            "child_prequential_false_prediction_row_ids": child_false.get(
                mode.value, []
            ),
            "child_graph_revocation_row_ids": child_revocations.get(
                mode.value, []
            ),
            "post_revocation_influence_count": 0,
            "sealed_evaluation_rows": decisions,
            "sealed_metrics": science.sealed_metrics(decisions),
            "frozen_organism_sha256": _sha_bytes(frozen_payloads[mode.value]),
            "serialization_restoration_exact": True,
            "r0_persistent_state_exact": True,
        }
    result = {
        key: value for key, value in prepared.items() if key != "authorities"
    } | {"status": "COMPLETED", "arms": arm_results}
    return result, frozen_payloads


def _shard_identity(
    attempt_id: str, stage: str, ordinal: int, seed: int, input_digest: str
) -> str:
    return _sha_json({
        "schema": SHARD_STATE_SCHEMA,
        "attempt_id": attempt_id,
        "stage": stage,
        "ordinal": ordinal,
        "seed": seed,
        "input_digest": input_digest,
    })


def _shard_paths(attempt_dir: Path, stage: str, ordinal: int) -> tuple[Path, Path]:
    root = attempt_dir / "shards" / stage.lower()
    return root / f"{ordinal:02d}.state.json", root / f"{ordinal:02d}.payload.pkl.gz"


def _read_completed_shard(
    attempt_dir: Path,
    stage: str,
    ordinal: int,
    expected_identity: str,
) -> tuple[dict[str, Any], Any]:
    state_path, payload_path = _shard_paths(attempt_dir, stage, ordinal)
    if not state_path.is_file():
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"missing {stage} shard state {ordinal}",
        )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("shard_identity") != expected_identity:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"{stage} shard identity mismatch {ordinal}",
        )
    if state.get("state") != "COMPLETED" or not payload_path.is_file():
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"{stage} shard {ordinal} is {state.get('state', 'MISSING')}",
        )
    payload_bytes = payload_path.read_bytes()
    if _sha_bytes(payload_bytes) != state["transport_sha256"]:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"{stage} shard transport mismatch {ordinal}",
        )
    payload = pickle.loads(gzip.decompress(payload_bytes))
    if _sha_json(payload["semantic_manifest"]) != state["output_digest"]:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"{stage} shard semantic mismatch {ordinal}",
        )
    return state, payload


_WORKER_SOURCE: TraceNativeCompetenceOrganism | None = None
_WORKER_STREAM: tuple[science.StreamRow, ...] = ()
_WORKER_CACHE: dict[str, CachedR0Observation] = {}
_WORKER_SOURCE_R0_DIGEST = ""
_WORKER_SOURCE_CONTINUATION_DIGEST = ""


def _worker_initialize(
    source_item: Mapping[str, Any],
    stream_manifests: Sequence[Mapping[str, Any]],
    cache_path: str,
) -> None:
    global _WORKER_SOURCE, _WORKER_STREAM, _WORKER_CACHE
    global _WORKER_SOURCE_R0_DIGEST, _WORKER_SOURCE_CONTINUATION_DIGEST
    # Mechanical normalization is the established deepcopy baseline.  Its
    # topology, weights, credit, lifecycle, action, and semantic trace are
    # exact; only retired construction-only triplet representation differs.
    _WORKER_SOURCE = copy.deepcopy(science._load_source(source_item))
    _WORKER_STREAM = tuple(
        science.StreamRow(**item) for item in stream_manifests
    )
    _WORKER_CACHE = load_and_verify_cache(
        Path(cache_path), _WORKER_SOURCE, _WORKER_STREAM
    )
    (
        _WORKER_SOURCE_R0_DIGEST,
        _WORKER_SOURCE_CONTINUATION_DIGEST,
    ) = _source_bindings(_WORKER_SOURCE)


def _claim_shard(
    state_path: Path,
    *,
    identity: str,
    attempt_id: str,
    stage: str,
    ordinal: int,
    seed: int,
    input_digest: str,
    source_digest: str | None = None,
    stream_digest: str | None = None,
) -> bool:
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("shard_identity") != identity:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"existing {stage} shard identity differs",
            )
        if state.get("state") == "COMPLETED":
            return False
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            f"{stage} shard {ordinal} may not rerun from {state.get('state')}",
        )
    _atomic_write_json(state_path, {
        "schema_version": SHARD_STATE_SCHEMA,
        "state": "STARTED",
        "attempt_id": attempt_id,
        "shard_identity": identity,
        "stage": stage,
        "ordinal": ordinal,
        "genome_seed": seed,
        "input_digest": input_digest,
        "source_digest": source_digest,
        "stream_digest": stream_digest,
        "started_unix_ns": time.time_ns(),
        "completed_unix_ns": None,
        "failed_unix_ns": None,
        "wall_seconds": None,
        "peak_rss_kib": None,
        "output_digest": None,
        "transport_sha256": None,
        "error": None,
    })
    return True


def _run_shard(
    attempt_dir_text: str,
    attempt_id: str,
    stage: str,
    ordinal: int,
    seed: int,
    input_digest: str,
) -> dict[str, Any]:
    if _WORKER_SOURCE is None:
        raise RuntimeError("worker source is not initialized")
    attempt_dir = Path(attempt_dir_text)
    identity = _shard_identity(attempt_id, stage, ordinal, seed, input_digest)
    state_path, payload_path = _shard_paths(attempt_dir, stage, ordinal)
    if not _claim_shard(
        state_path,
        identity=identity,
        attempt_id=attempt_id,
        stage=stage,
        ordinal=ordinal,
        seed=seed,
        input_digest=input_digest,
        source_digest=_WORKER_SOURCE_CONTINUATION_DIGEST,
        stream_digest=_sha_json([
            row.manifest() for row in _WORKER_STREAM
        ]),
    ):
        state, _payload = _read_completed_shard(
            attempt_dir, stage, ordinal, identity
        )
        return state
    started = time.perf_counter()
    try:
        if stage == "A":
            prepared = prepare_seed_cached(
                ordinal=ordinal,
                seed=seed,
                source=_WORKER_SOURCE,
                stream=_WORKER_STREAM,
                cache=_WORKER_CACHE,
            )
            authority_payloads = {
                mode.value: authority.dumps()
                for mode, authority in prepared["authorities"].items()
            }
            semantic = {
                key: value for key, value in prepared.items()
                if key != "authorities"
            } | {
                "authority_continuation_digests": {
                    mode.value: authority.continuation_digest()
                    for mode, authority in prepared["authorities"].items()
                }
            }
            payload = {
                "semantic_manifest": semantic,
                "authority_payloads": authority_payloads,
            }
        elif stage == "B":
            stage_a_identity = _shard_identity(
                attempt_id, "A", ordinal, seed, input_digest
            )
            _state_a, payload_a = _read_completed_shard(
                attempt_dir, "A", ordinal, stage_a_identity
            )
            prepared = {
                key: value for key, value in payload_a["semantic_manifest"].items()
                if key != "authority_continuation_digests"
            }
            prepared["authorities"] = {
                SpecializationMode(key): NativeProspectiveAuthorityV2.loads(value)
                for key, value in payload_a["authority_payloads"].items()
            }
            result, frozen_payloads = certify_and_evaluate_seed_cached(
                prepared,
                science.rows_by_region(
                    _WORKER_STREAM, "child_prospective_certification"
                ),
                science.rows_by_region(
                    _WORKER_STREAM, "sealed_read_only_evaluation"
                ),
                _WORKER_CACHE,
                source_r0_digest=_WORKER_SOURCE_R0_DIGEST,
                source_continuation_digest=(
                    _WORKER_SOURCE_CONTINUATION_DIGEST
                ),
            )
            payload = {
                "semantic_manifest": result,
                "frozen_authority_payloads": frozen_payloads,
            }
        else:
            raise ValueError(f"unknown shard stage {stage}")
        compressed = gzip.compress(
            pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL), mtime=0
        )
        _atomic_write_bytes(payload_path, compressed)
        state = {
            "schema_version": SHARD_STATE_SCHEMA,
            "state": "COMPLETED",
            "attempt_id": attempt_id,
            "shard_identity": identity,
            "stage": stage,
            "ordinal": ordinal,
            "genome_seed": seed,
            "input_digest": input_digest,
            "source_digest": _WORKER_SOURCE_CONTINUATION_DIGEST,
            "stream_digest": _sha_json([
                row.manifest() for row in _WORKER_STREAM
            ]),
            "started_unix_ns": json.loads(
                state_path.read_text(encoding="utf-8")
            )["started_unix_ns"],
            "completed_unix_ns": time.time_ns(),
            "failed_unix_ns": None,
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_kib": resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss,
            "output_digest": _sha_json(payload["semantic_manifest"]),
            "transport_sha256": _sha_bytes(compressed),
            "error": None,
        }
        _atomic_write_json(state_path, state)
        return state
    except BaseException as exc:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({
            "state": "FAILED",
            "failed_unix_ns": time.time_ns(),
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_kib": resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
        })
        _atomic_write_json(state_path, state)
        raise


def _canonical_aggregate_seed_results(
    results: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    ordered = sorted(
        (dict(item) for item in results), key=lambda item: int(item["ordinal"])
    )
    if [int(item["ordinal"]) for item in ordered] != list(range(len(ordered))):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "aggregate seed ordinals are incomplete or noncanonical",
        )
    return ordered


def prepare_performance_manifest(
    *, output: Path = SOURCE_MANIFEST
) -> dict[str, Any]:
    original = json.loads(science.SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if (
        _sha_file(science.SOURCE_MANIFEST) != ORIGINAL_SOURCE_MANIFEST_SHA256
        or _sha_file(science.RESULT_PATH) != ORIGINAL_RESULT_PLACEHOLDER_SHA256
        or _sha_file(science.SOURCE_PATH) != ORIGINAL_PROGRAM_SHA256
    ):
        raise RuntimeError("original frozen package is not byte-exact")
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "PERFORMANCE_RECLOSED_NOT_EXECUTED",
        "starting_commit": STARTING_COMMIT,
        "scientific_factor_changes": 0,
        "original_package": {
            "source_manifest_path": str(science.SOURCE_MANIFEST),
            "source_manifest_sha256": ORIGINAL_SOURCE_MANIFEST_SHA256,
            "result_placeholder_path": str(science.RESULT_PATH),
            "result_placeholder_sha256": ORIGINAL_RESULT_PLACEHOLDER_SHA256,
            "program_sha256": ORIGINAL_PROGRAM_SHA256,
            "preserved_byte_exact": True,
        },
        "frozen_science_identity": {
            "genome_seeds": original["seed_derivation"]["genome_seeds"],
            "stream_sha256": original["stream_sha256"],
            "stream_row_count": len(original["stream_rows"]),
            "stream_row_order": [row["row_id"] for row in original["stream_rows"]],
            "arms": original["arms"],
            "frozen_rules": original["frozen_rules"],
            "preregistration": original["preregistration"],
            "source_r0": original["source_r0"],
        },
        "cache_contract": {
            "schema_version": CACHE_SCHEMA,
            "constructed_only_inside_authorized_execution": True,
            "contains_outcome_or_competence_data": False,
            "one_observation_per_frozen_row": True,
            "each_organism_runs_own_v2_and_transaction": True,
        },
        "shard_contract": {
            "stages": ["A", "EXPOSURE_GATE", "B", "FINAL_AGGREGATE"],
            "seed_count": 32,
            "arms_coupled_per_seed_process": True,
            "parallelism_across_seeds_only": True,
            "maximum_workers": MAX_WORKERS,
            "precommitted_execution_workers": MAX_WORKERS,
            "worker_count_is_not_a_scientific_factor": True,
            "completed_shards_are_read_not_recomputed": True,
            "started_or_failed_shards_never_rerun": True,
            "stage_b_requires_all_stage_a_and_passing_gate": True,
        },
        "profile": profile,
        "profile_sha256": _sha_file(PROFILE_PATH),
        "source_hashes": {
            str(path): _sha_file(path) for path in DEPENDENCY_PATHS
        },
        "future_command": (
            "PYTHONPATH=src .venv/bin/python -m "
            "recon_lite_chess.autogrowth."
            "native_deferred_specialization_performance_reclosure "
            "--execute-frozen-shards --attempt-dir "
            f"{DEFAULT_ATTEMPT_DIR} --workers {MAX_WORKERS}"
        ),
        "fresh_cache_constructed": False,
        "stage_a_started": False,
        "fresh_outcomes_accessed": False,
        "execution_authorized": False,
    }
    payload["manifest_payload_sha256"] = _sha_json(payload)
    _atomic_write_json(output, payload)
    return payload


def prepare_result_placeholder(
    *, output: Path = RESULT_PLACEHOLDER
) -> dict[str, Any]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    original = json.loads(science.RESULT_PATH.read_text(encoding="utf-8"))
    payload = {
        **original,
        "schema_version": RESULT_SCHEMA,
        "status": "PERFORMANCE_RECLOSED_NOT_EXECUTED",
        "performance_source_manifest_path": str(SOURCE_MANIFEST),
        "performance_source_manifest_sha256": _sha_file(SOURCE_MANIFEST),
        "performance_manifest_payload_sha256": manifest[
            "manifest_payload_sha256"
        ],
        "original_result_placeholder_sha256": (
            ORIGINAL_RESULT_PLACEHOLDER_SHA256
        ),
        "fresh_cache_constructed": False,
        "stage_a_started": False,
        "stage_b_started": False,
        "execution_authorized": False,
    }
    _atomic_write_json(output, payload)
    return payload


def _verify_performance_manifest() -> tuple[dict[str, Any], dict[str, Any], tuple[science.StreamRow, ...]]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected = manifest.pop("manifest_payload_sha256")
    if _sha_json(manifest) != expected:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "performance manifest digest mismatch",
        )
    manifest["manifest_payload_sha256"] = expected
    for path, digest in manifest["source_hashes"].items():
        if _sha_file(path) != digest:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"performance source drift: {path}",
            )
    original, rows = science._verify_frozen_manifest()
    frozen = manifest["frozen_science_identity"]
    if (
        frozen["genome_seeds"] != original["seed_derivation"]["genome_seeds"]
        or frozen["stream_sha256"] != original["stream_sha256"]
        or frozen["stream_row_order"] != [row.row_id for row in rows]
        or frozen["arms"] != original["arms"]
        or frozen["frozen_rules"] != original["frozen_rules"]
    ):
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "performance reclosure changed frozen science",
        )
    return manifest, original, rows


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
        identity = _shard_identity(
            attempt_id, stage, ordinal, int(seed), input_digest
        )
        state_path, _payload_path = _shard_paths(attempt_dir, stage, ordinal)
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("shard_identity") != identity:
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    f"existing {stage} shard identity mismatch",
                )
            if state.get("state") == "COMPLETED":
                _read_completed_shard(attempt_dir, stage, ordinal, identity)
                continue
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                f"cannot resume {stage} shard {ordinal} from {state.get('state')}",
            )
        future = executor.submit(
            _run_shard,
            str(attempt_dir),
            attempt_id,
            stage,
            ordinal,
            int(seed),
            input_digest,
        )
        futures[future] = ordinal
    for future in as_completed(futures):
        future.result()


def _execute_frozen_shards(
    *,
    attempt_dir: Path = DEFAULT_ATTEMPT_DIR,
    workers: int = MAX_WORKERS,
) -> dict[str, Any]:
    if workers < 1 or workers > MAX_WORKERS:
        raise ValueError(f"workers must be in 1..{MAX_WORKERS}")
    manifest, original, rows = _verify_performance_manifest()
    source_item = original["source_r0"]["source_item"]
    seeds = tuple(map(int, original["seed_derivation"]["genome_seeds"]))
    attempt_id = _sha_json({
        "schema": ATTEMPT_SCHEMA,
        "performance_manifest_payload": manifest["manifest_payload_sha256"],
        "source_manifest_payload": original["manifest_payload_sha256"],
    })
    attempt_manifest_path = attempt_dir / "attempt.json"
    if attempt_manifest_path.exists():
        attempt = json.loads(attempt_manifest_path.read_text(encoding="utf-8"))
        if attempt.get("attempt_id") != attempt_id:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "attempt directory belongs to another immutable attempt",
            )
        if attempt.get("state") == "FAILED":
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "failed immutable attempt cannot be resumed",
            )
        if attempt.get("state") == "TERMINAL_STOP":
            return attempt
        if attempt.get("state") == "COMPLETED":
            final_path = Path(attempt["final_result_path"])
            if (
                not final_path.is_file()
                or _sha_file(final_path) != attempt["final_result_sha256"]
            ):
                raise science.ExperimentStop(
                    science.StopCategory.INSTRUMENT_STOP,
                    "completed aggregate is missing or changed",
                )
            return json.loads(final_path.read_text(encoding="utf-8"))
        if int(attempt.get("selected_workers", -1)) != workers:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "worker count is immutable after attempt creation",
            )
    else:
        attempt = {
            "schema_version": ATTEMPT_SCHEMA,
            "attempt_id": attempt_id,
            "state": "STARTED",
            "maximum_workers": MAX_WORKERS,
            "selected_workers": workers,
            "source_manifest_payload_sha256": original[
                "manifest_payload_sha256"
            ],
            "stream_sha256": original["stream_sha256"],
            "cache_state": "NOT_STARTED",
            "stage_a_state": "NOT_STARTED",
            "exposure_gate_state": "NOT_STARTED",
            "stage_b_state": "NOT_STARTED",
            "final_aggregate_state": "NOT_STARTED",
        }
        _atomic_write_json(attempt_manifest_path, attempt)
    cache_path = attempt_dir / "r0_observation_cache.json"
    if attempt["cache_state"] == "NOT_STARTED":
        attempt["cache_state"] = "STARTED"
        _atomic_write_json(attempt_manifest_path, attempt)
        source = copy.deepcopy(science._load_source(source_item))
        observations = build_observation_cache(
            source, rows, frame_namespace=f"fresh-cache:{attempt_id}"
        )
        _atomic_write_json(cache_path, cache_payload(source, rows, observations))
        attempt["cache_state"] = "COMPLETED"
        attempt["cache_sha256"] = _sha_file(cache_path)
        _atomic_write_json(attempt_manifest_path, attempt)
    elif attempt["cache_state"] == "COMPLETED":
        if not cache_path.is_file() or _sha_file(cache_path) != attempt["cache_sha256"]:
            raise science.ExperimentStop(
                science.StopCategory.INSTRUMENT_STOP,
                "completed cache is missing or changed",
            )
    else:
        raise science.ExperimentStop(
            science.StopCategory.INSTRUMENT_STOP,
            "interrupted cache construction cannot be rerun",
        )
    input_digest = _sha_json({
        "attempt_id": attempt_id,
        "cache_sha256": attempt["cache_sha256"],
        "stream_sha256": original["stream_sha256"],
        "source_item": source_item,
    })
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_initialize,
        initargs=(
            source_item,
            [row.manifest() for row in rows],
            str(cache_path),
        ),
    ) as executor:
        attempt["stage_a_state"] = "STARTED"
        _atomic_write_json(attempt_manifest_path, attempt)
        _run_stage_pool(
            executor,
            attempt_dir=attempt_dir,
            attempt_id=attempt_id,
            stage="A",
            seeds=seeds,
            input_digest=input_digest,
        )
        stage_a_payloads = []
        for ordinal, seed in enumerate(seeds):
            identity = _shard_identity(
                attempt_id, "A", ordinal, seed, input_digest
            )
            _state, payload = _read_completed_shard(
                attempt_dir, "A", ordinal, identity
            )
            stage_a_payloads.append(payload["semantic_manifest"])
        attempt["stage_a_state"] = "COMPLETED"
        exposure = science.paired_exposure_admission(
            [item["exposure"] for item in stage_a_payloads]
        )
        attempt["exposure_gate"] = exposure
        attempt["exposure_gate_state"] = (
            "PASSED" if exposure["passed"] else "FAILED"
        )
        _atomic_write_json(attempt_manifest_path, attempt)
        if not exposure["passed"]:
            attempt["state"] = "TERMINAL_STOP"
            attempt["conclusion"] = (
                science.StopCategory.PAIRED_CHILD_EVIDENCE_STARVATION.value
            )
            _atomic_write_json(attempt_manifest_path, attempt)
            return attempt
        attempt["stage_b_state"] = "STARTED"
        _atomic_write_json(attempt_manifest_path, attempt)
        _run_stage_pool(
            executor,
            attempt_dir=attempt_dir,
            attempt_id=attempt_id,
            stage="B",
            seeds=seeds,
            input_digest=input_digest,
        )
    seed_results = []
    for ordinal, seed in enumerate(seeds):
        identity = _shard_identity(
            attempt_id, "B", ordinal, seed, input_digest
        )
        _state, payload = _read_completed_shard(
            attempt_dir, "B", ordinal, identity
        )
        seed_results.append(payload["semantic_manifest"])
    seed_results = _canonical_aggregate_seed_results(seed_results)
    attempt["stage_b_state"] = "COMPLETED"
    adjudication = science._adjudicate(seed_results, attempt["exposure_gate"])
    final = {
        "schema_version": RESULT_SCHEMA,
        "status": "COMPLETED",
        "attempt_id": attempt_id,
        "source_manifest_payload_sha256": original["manifest_payload_sha256"],
        "stream_sha256": original["stream_sha256"],
        "seeds": seed_results,
        "adjudication": adjudication,
        "conclusion": adjudication["conclusion"],
    }
    final_path = attempt_dir / "final_result.json"
    _atomic_write_json(final_path, final)
    attempt.update({
        "state": "COMPLETED",
        "final_aggregate_state": "COMPLETED",
        "final_result_path": str(final_path),
        "final_result_sha256": _sha_file(final_path),
        "conclusion": adjudication["conclusion"],
    })
    _atomic_write_json(attempt_manifest_path, attempt)
    return final


def execute_frozen_shards(
    *,
    attempt_dir: Path = DEFAULT_ATTEMPT_DIR,
    workers: int = MAX_WORKERS,
) -> dict[str, Any]:
    """Run or read one immutable attempt and persist terminal failure state."""

    try:
        return _execute_frozen_shards(
            attempt_dir=attempt_dir,
            workers=workers,
        )
    except BaseException as exc:
        attempt_manifest_path = attempt_dir / "attempt.json"
        if attempt_manifest_path.is_file():
            attempt = json.loads(
                attempt_manifest_path.read_text(encoding="utf-8")
            )
            if attempt.get("state") not in {
                "COMPLETED", "FAILED", "TERMINAL_STOP"
            }:
                attempt.update({
                    "state": "FAILED",
                    "failed_unix_ns": time.time_ns(),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                })
                _atomic_write_json(attempt_manifest_path, attempt)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare-performance-manifest", action="store_true")
    group.add_argument("--prepare-result-placeholder", action="store_true")
    group.add_argument("--execute-frozen-shards", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--attempt-dir", type=Path, default=DEFAULT_ATTEMPT_DIR)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    if args.prepare_performance_manifest:
        result = prepare_performance_manifest(
            output=args.output or SOURCE_MANIFEST
        )
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
            SOURCE_MANIFEST if args.prepare_performance_manifest
            else RESULT_PLACEHOLDER if args.prepare_result_placeholder
            else args.attempt_dir
        )),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
