from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import json
from pathlib import Path

import chess
import pytest

from recon_lite import FrameContext, FrameKind

from recon_lite_chess.autogrowth import (
    native_deferred_specialization_fresh_discriminator as science,
)
from recon_lite_chess.autogrowth import (
    native_deferred_specialization_performance_reclosure as performance,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_deferred_specialization_development_canary import (
    _bind_semantic_reference_digests,
    _controlled_discovery_source,
    _load_regression,
    _load_source,
    _source_item,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)


@pytest.fixture(scope="module")
def viewed_fixture():
    item = _source_item()
    source = _load_source(item)
    references = tuple(_bind_semantic_reference_digests(
        _load_regression()["reference_rows"], item
    ))
    rows = tuple(
        science.StreamRow(
            region="viewed_development",
            region_ordinal=ordinal,
            global_ordinal=ordinal,
            row_id=f"viewed-profile-{ordinal:02d}",
            predecessor_fen=str(reference["fen"]),
            d4_orbit_key=science.canonical_d4_orbit_key(
                str(reference["fen"])
            ),
            planned_physical_interaction_id=f"viewed-profile-{ordinal:02d}",
        )
        for ordinal, reference in enumerate(references[:2])
    )
    return source, references[:2], rows


def _authority(source):
    base = _controlled_discovery_source(source)
    authority = NativeProspectiveAuthorityV2.from_organism(
        base,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        structural_epoch_schedule=(69,),
    )
    authority.close_nomination()
    return authority


def test_original_frozen_package_remains_byte_exact():
    assert performance._sha_file(science.SOURCE_MANIFEST) == (
        performance.ORIGINAL_SOURCE_MANIFEST_SHA256
    )
    assert performance._sha_file(science.RESULT_PATH) == (
        performance.ORIGINAL_RESULT_PLACEHOLDER_SHA256
    )
    assert performance._sha_file(science.SOURCE_PATH) == (
        performance.ORIGINAL_PROGRAM_SHA256
    )


def test_cache_is_outcome_and_competence_free_and_fully_bound(viewed_fixture):
    source, _references, rows = viewed_fixture
    observations = performance.build_observation_cache(
        source, rows[:1], frame_namespace="viewed-cache-contract"
    )
    record = observations[0]
    assert not performance.FORBIDDEN_CACHE_KEYS.intersection(record.manifest())
    assert record.row_id == rows[0].row_id
    assert record.predecessor_fen == rows[0].predecessor_fen
    assert set(record.source_r0_component_digests) == set(
        performance.R0_SEMANTIC_AUDIT_FIELDS
    )
    assert performance._sha_json(record.source_r0_component_digests) == (
        record.source_r0_persistent_digest
    )
    assert record.actuation == record.trace_manifest["actuation"]
    assert record.ordered_signal_identities == tuple(
        item["identity"] for item in record.terminal_signals
    )
    assert record.terminal_source_identities == tuple(
        item["source_node_identity"] for item in record.terminal_signals
    )
    assert record.semantic_trace_digest == science._trace_digest(record.trace())


def test_live_and_cached_real_event_are_exact_through_final_state(viewed_fixture):
    source, reference_rows, rows = viewed_fixture
    row = rows[0]
    record = performance.build_observation_cache(
        source, (row,), frame_namespace="viewed-live-cache-parity"
    )[0]
    live = _authority(source)
    cached = copy.deepcopy(live)
    live_pending, live_trace = live.open_real_event(FrameContext(
        record.frame_id,
        FrameKind.REAL,
        values={"board": chess.Board(row.predecessor_fen)},
    ))
    source_r0_digest, source_continuation_digest = (
        performance._source_bindings(source)
    )
    cached_pending, cached_trace = performance.open_cached_real_event(
        cached,
        row,
        record,
        source_r0_digest=source_r0_digest,
        source_continuation_digest=source_continuation_digest,
    )
    assert live_trace.actuation == cached_trace.actuation
    assert live_trace.ordered_signal_identities == (
        cached_trace.ordered_signal_identities
    )
    assert live_trace.terminal_signals == cached_trace.terminal_signals
    assert live_trace.source_organism_identity == (
        cached_trace.source_organism_identity
    )
    assert live_trace.source_state_identity == cached_trace.source_state_identity
    assert science._trace_digest(live_trace) == science._trace_digest(cached_trace)
    assert live_pending.matching_cell_ids == cached_pending.matching_cell_ids
    assert live_pending.pre_outcome_classification == (
        cached_pending.pre_outcome_classification
    )
    board = chess.Board(row.predecessor_fen)
    live_successor = science._execute_transition(board, live_trace)
    cached_successor = science._execute_transition(board, cached_trace)
    assert live_successor.fen() == cached_successor.fen() == record.successor_fen
    assert live_successor.is_checkmate() == bool(
        reference_rows[0]["actual_completion"]
    )
    live_receipt = live.mint_environment_receipt(
        pending_token=live_pending.pending_token,
        trace=live_trace,
        predecessor=board,
        successor=live_successor,
    )
    cached_receipt = cached.mint_environment_receipt(
        pending_token=cached_pending.pending_token,
        trace=cached_trace,
        predecessor=board,
        successor=cached_successor,
    )
    assert live_receipt.manifest() == cached_receipt.manifest()
    live.consume(live_receipt)
    cached.consume(cached_receipt)
    assert live.continuation_manifest() == cached.continuation_manifest()


def test_live_and_cached_sealed_evaluation_match_without_mutation(viewed_fixture):
    source, _reference_rows, rows = viewed_fixture
    row = rows[1]
    record = performance.build_observation_cache(
        source, (row,), frame_namespace="viewed-evaluation-parity"
    )[0]
    live = _authority(source)
    live.seal_read_only_evaluation()
    cached = copy.deepcopy(live)
    before = cached.continuation_manifest()
    live_opened = live.evaluate_sealed_real(FrameContext(
        record.frame_id,
        FrameKind.REAL,
        values={"board": chess.Board(row.predecessor_fen)},
    ))
    r0_digest, continuation_digest = performance._source_bindings(source)
    cached_opened = performance.evaluate_cached_observation(
        cached,
        row,
        record,
        source_r0_digest=r0_digest,
        source_continuation_digest=continuation_digest,
    )
    assert live_opened["commitment"].trace.actuation == (
        cached_opened["trace"].actuation
    )
    assert live_opened["commitment"].trace.terminal_signals == (
        cached_opened["trace"].terminal_signals
    )
    assert live_opened["graph_emissions"] == cached_opened["graph"]
    assert live_opened["classification"] == cached_opened["classification"]
    assert cached.continuation_manifest() == before


def test_live_virtual_exposure_and_cached_graph_are_exact(viewed_fixture):
    source, _reference_rows, rows = viewed_fixture
    row = rows[0]
    record = performance.build_observation_cache(
        source, (row,), frame_namespace="viewed-exposure-parity"
    )[0]
    live = _authority(source)
    cached = copy.deepcopy(live)
    live_before = live.continuation_manifest()
    cached_before = cached.continuation_manifest()
    opened = live.open_virtual(FrameContext(
        record.frame_id,
        FrameKind.VIRTUAL,
        values={"board": chess.Board(row.predecessor_fen)},
    ))
    r0_digest, continuation_digest = performance._source_bindings(source)
    trace = performance._validate_cache_record(
        record,
        source_r0_digest=r0_digest,
        source_continuation_digest=continuation_digest,
        row=row,
    )
    graph = cached._graph_measure(trace)
    classification = cached._classification_from_emissions(
        cached.states, graph
    )
    assert science._semantic_trace_manifest(
        opened["query"].graph_signal_trace
    ) == science._semantic_trace_manifest(trace)
    assert opened["graph_emissions"] == graph
    assert opened["classification"] == classification
    assert live.continuation_manifest() == live_before
    assert cached.continuation_manifest() == cached_before


def test_cache_tampering_fails_closed(viewed_fixture):
    source, _references, rows = viewed_fixture
    record = performance.build_observation_cache(
        source, rows[:1], frame_namespace="viewed-cache-tamper"
    )[0]
    damaged = replace(record, predecessor_fen=rows[1].predecessor_fen)
    r0_digest, continuation_digest = performance._source_bindings(source)
    with pytest.raises(science.ExperimentStop, match="binding mismatch"):
        performance._validate_cache_record(
            damaged,
            source_r0_digest=r0_digest,
            source_continuation_digest=continuation_digest,
            row=rows[0],
        )


@pytest.mark.parametrize("state", ["STARTED", "FAILED"])
def test_started_or_failed_shard_can_never_rerun(tmp_path, state):
    attempt_id = "attempt"
    input_digest = "input"
    identity = performance._shard_identity(
        attempt_id, "A", 0, 11, input_digest
    )
    state_path, _payload_path = performance._shard_paths(tmp_path, "A", 0)
    performance._atomic_write_json(state_path, {
        "shard_identity": identity,
        "state": state,
    })
    with pytest.raises(science.ExperimentStop, match="may not rerun"):
        performance._claim_shard(
            state_path,
            identity=identity,
            attempt_id=attempt_id,
            stage="A",
            ordinal=0,
            seed=11,
            input_digest=input_digest,
        )


def test_completed_shard_is_read_not_recomputed(tmp_path):
    state_path, _payload_path = performance._shard_paths(tmp_path, "A", 0)
    identity = performance._shard_identity("attempt", "A", 0, 11, "input")
    performance._atomic_write_json(state_path, {
        "shard_identity": identity,
        "state": "COMPLETED",
    })
    assert performance._claim_shard(
        state_path,
        identity=identity,
        attempt_id="attempt",
        stage="A",
        ordinal=0,
        seed=11,
        input_digest="input",
    ) is False


def test_stage_and_seed_shard_identities_are_immutable_and_distinct():
    identities = {
        performance._shard_identity("attempt", stage, ordinal, seed, "input")
        for stage in ("A", "B")
        for ordinal, seed in enumerate((11, 12))
    }
    assert len(identities) == 4


def test_aggregate_artifact_is_exact_across_sequential_two_worker_and_reverse(
    viewed_fixture,
):
    source, _references, rows = viewed_fixture
    observations = performance.build_observation_cache(
        source, rows, frame_namespace="viewed-schedule-parity"
    )
    viewed_records = [{
        "ordinal": ordinal,
        "genome_seed": 100 + ordinal,
        "viewed_row_id": observation.row_id,
        "viewed_record_digest": observation.record_digest,
        "semantic_trace_digest": observation.semantic_trace_digest,
    } for ordinal, observation in enumerate(observations)]
    sequential = performance._canonical_aggregate_seed_results(viewed_records)
    with ThreadPoolExecutor(max_workers=2) as executor:
        two_worker = list(executor.map(lambda item: dict(item), viewed_records))
    two_worker = performance._canonical_aggregate_seed_results(two_worker)
    reverse = performance._canonical_aggregate_seed_results(
        reversed(viewed_records)
    )
    assert json.dumps(sequential, sort_keys=True) == json.dumps(
        two_worker, sort_keys=True
    ) == json.dumps(reverse, sort_keys=True)


def test_exposure_gate_keeps_all_32_and_never_selects_subset():
    rows = [
        {"ordinal": ordinal, "local_count": 4, "blind_count": 4}
        for ordinal in range(32)
    ]
    gate = science.paired_exposure_admission(rows)
    assert gate["passed"] is True
    assert gate["subset_selection_permitted"] is False
    assert gate["analysis_ordinals"] == list(range(32))


def test_worker_cap_is_memory_only_and_not_a_scientific_factor():
    assert performance.MAX_WORKERS == 8
    assert "workers" not in science.FROZEN_VALIDATION_RECORD


def test_performance_manifest_preserves_exact_science_when_present():
    if not performance.SOURCE_MANIFEST.is_file():
        pytest.skip("performance manifest is generated after focused tests")
    manifest = json.loads(performance.SOURCE_MANIFEST.read_text(encoding="utf-8"))
    original = json.loads(science.SOURCE_MANIFEST.read_text(encoding="utf-8"))
    frozen = manifest["frozen_science_identity"]
    assert frozen["genome_seeds"] == original["seed_derivation"]["genome_seeds"]
    assert frozen["stream_sha256"] == original["stream_sha256"]
    assert frozen["arms"] == original["arms"]
    assert frozen["frozen_rules"] == original["frozen_rules"]
    assert manifest["fresh_cache_constructed"] is False
    assert manifest["stage_a_started"] is False
    assert manifest["fresh_outcomes_accessed"] is False
    assert manifest["shard_contract"]["precommitted_execution_workers"] == 8
