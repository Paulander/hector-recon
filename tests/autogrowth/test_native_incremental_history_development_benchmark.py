from __future__ import annotations

import copy
from contextlib import contextmanager
import json
import time
from types import SimpleNamespace

import chess
import pytest

from recon_lite_chess.autogrowth import (
    native_deferred_specialization_performance_reclosure as cache_api,
)
from recon_lite_chess.autogrowth import (
    native_incremental_history_development_benchmark as benchmark,
)
from tests.autogrowth.test_native_incremental_history_validation import (
    _synthetic_authority,
)


def test_stream_is_deterministic_labeled_and_materially_disjoint() -> None:
    first = benchmark.build_development_stream()
    second = benchmark.build_development_stream()

    assert first.manifest == second.manifest
    assert first.rows == second.rows
    assert first.manifest["label"] == benchmark.DEVELOPMENT_LABEL
    assert first.manifest["scientific_use_permitted"] is False
    assert first.manifest["construction_seed"] == 16591302007524402855
    assert first.manifest["opened_protected_resources"] == []
    assert first.manifest["performance_scope_disclosure"][
        "engagement_is_constructed_not_naturalistic"
    ] is True
    assert first.manifest["cache_disclosure"][
        "outcome_derivable_from_successor_fen"
    ] is True
    assert len(first.rows) == sum(benchmark.REGION_COUNTS.values())
    assert len({row.row_id for row in first.rows}) == len(first.rows)
    assert len({row.predecessor_fen for row in first.rows}) == len(first.rows)
    assert all(benchmark.DEVELOPMENT_LABEL in row.row_id for row in first.rows)
    for row in first.rows:
        board = chess.Board(row.predecessor_fen)
        assert sorted(piece.symbol() for piece in board.piece_map().values()) == [
            "K", "R", "k", "n"
        ]
        assert board.pieces(chess.KNIGHT, chess.BLACK)


def test_development_genome_seeds_are_outside_frozen_namespace() -> None:
    seeds = [benchmark.development_seed(index) for index in range(9)]
    assert len(set(seeds)) == len(seeds)
    assert all(seed >= 2**63 for seed in seeds)
    assert all(seed < 2**64 for seed in seeds)
    with pytest.raises(ValueError):
        benchmark.development_seed(-1)


def test_self_digest_atomic_roundtrip_and_tamper_failure(tmp_path) -> None:
    path = tmp_path / "nested" / "result.json"
    payload = benchmark._self_digest({
        "schema_version": "test",
        "label": benchmark.DEVELOPMENT_LABEL,
        "status": "COMPLETED",
    })
    benchmark._atomic_write_json(path, payload)
    assert benchmark._load_self_digested(path) == payload

    changed = json.loads(path.read_text(encoding="utf-8"))
    changed["status"] = "CHANGED"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(RuntimeError, match="self-digest mismatch"):
        benchmark._load_self_digested(path)


def test_output_guard_rejects_every_path_outside_development_tree(
    tmp_path,
) -> None:
    with pytest.raises(RuntimeError, match="benchmark output"):
        benchmark._guard_output_dir(tmp_path)
    with pytest.raises(RuntimeError, match="benchmark output"):
        benchmark._guard_output_dir(benchmark.ALLOWED_OUTPUT_ROOT)
    accepted = benchmark.ALLOWED_OUTPUT_ROOT / "unit-test-only"
    assert benchmark._guard_output_dir(accepted) == accepted.resolve()


def test_tiny_marked_cache_preserves_declared_outcomes_and_marker() -> None:
    full = benchmark.build_development_stream()
    selected_indices = (0, 1)
    tiny = benchmark.DevelopmentStream(
        rows=tuple(full.rows[index] for index in selected_indices),
        families=tuple(full.families[index] for index in selected_indices),
        training_cases=full.training_cases,
        manifest={
            **full.manifest,
            "stream_sha256": "tiny-development-only-canary",
        },
    )
    source = benchmark.build_development_source(tiny)
    cache = benchmark.build_and_validate_cache(source, tiny)
    benchmark._validate_cached_outcomes(tiny, cache)
    assert [
        chess.Board(cache[row.row_id].successor_fen).is_checkmate()
        for row in tiny.rows
    ] == [True, False]
    assert all(
        chess.Board(cache[row.row_id].successor_fen).pieces(
            chess.KNIGHT, chess.BLACK
        )
        for row in tiny.rows
    )


def test_profiled_consume_and_additive_chain_rebuild_are_exact() -> None:
    authority = _synthetic_authority()
    row = benchmark.science.StreamRow(
        region="development_unit",
        region_ordinal=0,
        global_ordinal=0,
        row_id=f"{benchmark.DEVELOPMENT_LABEL}:profiled-unit",
        predecessor_fen=(
            "8/8/8/8/8/7K/5R2/7k w - - 0 20"
        ),
        d4_orbit_key=benchmark.science.canonical_d4_orbit_key(
            "8/8/8/8/8/7K/5R2/7k w - - 0 20"
        ),
        planned_physical_interaction_id="profiled-unit",
    )
    source = authority.base
    record = cache_api.build_observation_cache(
        source, (row,), frame_namespace=benchmark.DEVELOPMENT_LABEL
    )[0]
    r0_digest, continuation_digest = cache_api._source_bindings(source)
    differential = benchmark._profiled_consume_differential(
        authority,
        row,
        record,
        source_r0_digest=r0_digest,
        source_continuation_digest=continuation_digest,
    )
    assert differential["exact"] is True
    benchmark._plain_event(
        authority,
        row,
        record,
        source_r0_digest=r0_digest,
        source_continuation_digest=continuation_digest,
    )
    projection = benchmark._checkpoint_projection(authority)
    assert projection["additive_history_chain_rebuild_exact"] is True
    assert projection["live_history_manifest"] == projection[
        "rebuilt_history_manifest"
    ]


def test_run_plan_freezes_workers_cohort_and_seed_identity(tmp_path) -> None:
    identity = {"input_identity_sha256": "input"}
    plan = benchmark._load_or_create_run_plan(
        output_dir=tmp_path,
        input_identity=identity,
        cohort_size=2,
        workers=1,
        calibration_decision_sha256="calibration",
    )
    same = benchmark._load_or_create_run_plan(
        output_dir=tmp_path,
        input_identity=identity,
        cohort_size=2,
        workers=1,
        calibration_decision_sha256="calibration",
    )
    assert same == plan
    with pytest.raises(RuntimeError, match="immutable"):
        benchmark._load_or_create_run_plan(
            output_dir=tmp_path,
            input_identity=identity,
            cohort_size=2,
            workers=2,
            calibration_decision_sha256="calibration",
        )
    first = benchmark._seed_identity(
        identity,
        ordinal=1,
        seed=benchmark.development_seed(1),
        run_plan_sha256=plan["run_plan_sha256"],
    )
    second = benchmark._seed_identity(
        identity,
        ordinal=1,
        seed=benchmark.development_seed(1),
        run_plan_sha256="different-plan",
    )
    assert first != second


def test_phase1_cli_defaults_to_bounded_gate_and_requires_continuation() -> None:
    gate = benchmark._parse_args(["--phase1"])
    assert gate.phase1 is True
    assert gate.continue_phase1_to is None
    assert gate.max_wall_seconds == 7200.0
    assert gate.max_peak_rss_mib == 8192.0

    continued = benchmark._parse_args([
        "--continue-phase1-to", "64",
        "--max-wall-seconds", "3600",
        "--max-peak-rss-mib", "4096",
    ])
    assert continued.phase1 is False
    assert continued.continue_phase1_to == 64
    assert continued.max_wall_seconds == 3600.0
    assert continued.max_peak_rss_mib == 4096.0


def test_phase1_claims_separate_event_and_boundary_coverage() -> None:
    claims = benchmark._phase1_claim_scope((32, 64))
    assert claims["per_event_legacy_incremental_exact_parity"][
        "covered_event_range_inclusive"
    ] == [1, 32]
    assert claims["incremental_execution"][
        "covered_event_range_inclusive"
    ] == [1, 64]
    assert claims["full_history_boundary_reconstruction"][
        "covered_event_counts"
    ] == [32, 64]
    assert claims["unexecuted_events_not_claimed"] == [65, 256]
    assert claims[
        "checkpoint_success_does_not_imply_per_event_strategy_parity"
    ] is True


def test_phase1_32_to_64_continuation_is_incremental_only_with_boundary(
    monkeypatch,
) -> None:
    class FakeAuthority:
        def __init__(self, count: int, mode: str) -> None:
            self.count = count
            self._history_validation_mode = mode
            self.boundaries = []

        def continuation_manifest(self):
            return {"event_count": self.count}

        def verify_full_history_boundary(self, boundary: str) -> None:
            self.boundaries.append(boundary)

        def dumps(self) -> bytes:
            return json.dumps({
                "count": self.count,
                "mode": self._history_validation_mode,
            }).encode("utf-8")

        @staticmethod
        def loads(payload: bytes):
            item = json.loads(payload.decode("utf-8"))
            return FakeAuthority(item["count"], item["mode"])

        def set_history_validation_mode_for_development(
            self, mode: str
        ) -> None:
            self._history_validation_mode = mode

        def seal_read_only_evaluation(self) -> None:
            return None

    parents = tuple(
        SimpleNamespace(row_id=f"parent-{index}") for index in range(5)
    )
    certifications = tuple(
        SimpleNamespace(row_id=f"certification-{index}")
        for index in range(251)
    )

    def _rows(_stream, region):
        if region == "parent_prospective_support_and_contradiction":
            return parents
        if region == "child_prospective_certification":
            return certifications
        if region == "sealed_evaluation":
            return ()
        raise AssertionError(region)

    @contextmanager
    def _attribution():
        yield object()

    consumed_strategies = []

    def _profiled_event(authority, row, _record, **_kwargs):
        consumed_strategies.append(authority._history_validation_mode)
        authority.count += 1
        trace = {"row_id": row.row_id}
        return {
            "pending": {"row_id": row.row_id},
            "trace": trace,
            "receipt": {"row_id": row.row_id},
            "emission": {"row_id": row.row_id},
            "actual": False,
            "timing": {"event_wall_seconds": 0.0},
        }

    monkeypatch.setattr(benchmark, "_rows_by_region", _rows)
    monkeypatch.setattr(benchmark, "_runtime_attribution", _attribution)
    monkeypatch.setattr(benchmark, "_profiled_event", _profiled_event)
    monkeypatch.setattr(
        benchmark, "_history_event_count", lambda authority: authority.count
    )
    monkeypatch.setattr(
        benchmark, "_topology_size", lambda _authority: {
            "candidate_count": 1,
            "graph_node_count": 1,
            "graph_edge_count": 0,
        }
    )
    monkeypatch.setattr(
        benchmark,
        "_checkpoint_projection",
        lambda authority: {"event_count": authority.count},
    )
    monkeypatch.setattr(
        benchmark.science, "_semantic_trace_manifest", lambda trace: trace
    )
    monkeypatch.setattr(
        benchmark.NativeProspectiveAuthorityV2,
        "loads",
        staticmethod(FakeAuthority.loads),
    )
    monkeypatch.setattr(benchmark, "_rss_mib", lambda: (1.0, "unit"))

    strategies = {
        mode: {
            "incremental": FakeAuthority(
                32, benchmark.HISTORY_VALIDATION_INCREMENTAL
            )
        }
        for mode in benchmark.ARMS
    }
    all_rows = (*parents, *certifications)
    cache = {row.row_id: object() for row in all_rows}
    result, continued = benchmark._run_phase1_stage(
        source=None,
        stream=SimpleNamespace(manifest={"stream_sha256": "unit"}),
        cache=cache,
        maximum_events=64,
        starting_event=32,
        starting_strategies=strategies,
        starting_discovery={
            "source_r0_digest": "r0",
            "source_continuation_digest": "continuation",
        },
    )

    assert set(consumed_strategies) == {
        benchmark.HISTORY_VALIDATION_INCREMENTAL
    }
    assert len(consumed_strategies) == 32 * len(benchmark.ARMS)
    assert result["post_gate_incremental_only"] is True
    assert result["claim_scope"][
        "per_event_legacy_incremental_exact_parity"
    ]["covered_event_range_inclusive"] is None
    assert result["claim_scope"]["full_history_boundary_reconstruction"][
        "covered_event_counts"
    ] == [64]
    assert all(
        set(pair) == {"incremental"} for pair in continued.values()
    )
    assert all(
        pair["incremental"].count == 64 for pair in continued.values()
    )


def test_phase1_checkpoint_state_roundtrip_preserves_validation_modes() -> None:
    authority = _synthetic_authority()
    strategies = {}
    for mode in benchmark.ARMS:
        incremental = copy.deepcopy(authority)
        legacy = copy.deepcopy(authority)
        incremental.set_history_validation_mode_for_development(
            benchmark.HISTORY_VALIDATION_INCREMENTAL
        )
        legacy.set_history_validation_mode_for_development(
            benchmark.HISTORY_VALIDATION_LEGACY
        )
        strategies[mode] = {
            "incremental": incremental,
            "legacy_full_replay": legacy,
        }

    states, timings = benchmark._serialize_phase1_strategies(
        strategies, expected_event_count=0
    )
    restored = benchmark._restore_phase1_strategies(
        {"authority_states": states}, expected_event_count=0
    )
    assert all(
        item["roundtrip_exact"] is True
        for pair in timings.values()
        for item in pair.values()
    )
    for mode in benchmark.ARMS:
        assert (
            restored[mode]["incremental"].continuation_manifest()
            == restored[mode]["legacy_full_replay"].continuation_manifest()
        )
        assert restored[mode][
            "incremental"
        ]._history_validation_mode == benchmark.HISTORY_VALIDATION_INCREMENTAL
        assert restored[mode][
            "legacy_full_replay"
        ]._history_validation_mode == benchmark.HISTORY_VALIDATION_LEGACY


def test_phase1_hard_wall_ceiling_interrupts_in_flight_work() -> None:
    with pytest.raises(
        benchmark.Phase1CeilingExceeded,
        match="hard wall ceiling",
    ):
        with benchmark._phase1_wall_budget(
            max_wall_seconds=0.01,
            max_peak_rss_mib=10**9,
        ):
            time.sleep(0.1)


def test_phase1_atomic_checkpoint_chain_builds_bounded_index(tmp_path) -> None:
    identity = "phase1-chain-unit"
    previous_digest = None
    for start, end in ((0, 32), (32, 64)):
        stage = {
            "stream_sha256": "development-stream",
            "genome_seed": benchmark.development_seed(0),
            "initialization_wall_seconds": 1.0 if start == 0 else 0.0,
            "structural": {"unit": {"exact": True}} if start == 0 else {},
            "checkpoints": {str(end): {"unit": {"exact": True}}},
            "midpoint_serialization_restoration": {},
            "profiled_consume_public_differential": {
                "history_zero": {"exact": True} if start == 0 else None,
                "history_128_after_structural_growth": None,
            },
            "sealed_evaluation": {"unit": {"exact": True}},
            "event_timings": {
                mode.value: {
                    strategy: []
                    for strategy in benchmark.PHASE1_STRATEGIES
                }
                for mode in benchmark.ARMS
            },
            "started_at": f"start-{end}",
            "finished_at": f"finish-{end}",
            "wall_seconds": float(end - start),
            "cpu_seconds": float(end - start),
            "peak_rss_mib": float(end),
            "peak_rss_basis": "unit",
        }
        checkpoint = benchmark._self_digest({
            "schema_version": benchmark.PHASE1_CHECKPOINT_SCHEMA,
            "status": "PASSED",
            "input_identity_sha256": identity,
            "checkpoint_event_count": end,
            "previous_checkpoint_event_count": start,
            "previous_checkpoint_payload_digest": previous_digest,
            "discovery": {"unit": True},
            "stage_result": stage,
            "authority_states": {},
        })
        benchmark._atomic_write_json(
            benchmark._phase1_checkpoint_path(tmp_path, end), checkpoint
        )
        previous_digest = checkpoint["payload_digest"]

    index = benchmark._build_phase1_index(
        output_dir=tmp_path,
        input_identity_sha256=identity,
        maximum_events=64,
    )
    assert index["status"] == "PASSED"
    assert index["coverage_status"] == (
        "BOUNDED_32_EVENT_GATE_WITH_EXPLICIT_BOUNDARIES"
    )
    assert index["checkpoint_event_counts"] == [32, 64]
    assert index["claim_scope"][
        "per_event_legacy_incremental_exact_parity"
    ][
        "covered_event_range_inclusive"
    ] == [1, 32]
    assert index["next_checkpoint_event_count"] == 128


def test_phase1_ceiling_failure_keeps_partial_state_nonresumable(
    tmp_path, monkeypatch
) -> None:
    def _raise_ceiling(**_kwargs):
        raise benchmark.Phase1CeilingExceeded("unit ceiling")

    monkeypatch.setattr(benchmark, "_run_phase1_stage", _raise_ceiling)
    with pytest.raises(benchmark.Phase1CeilingExceeded, match="unit ceiling"):
        benchmark._write_phase1_stage(
            output_dir=tmp_path,
            source=None,
            stream=None,
            cache={},
            input_identity={"input_identity_sha256": "unit-input"},
            target_event_count=32,
            continuing=False,
            max_wall_seconds=60.0,
            max_peak_rss_mib=10**9,
        )

    assert not benchmark._phase1_checkpoint_path(tmp_path, 32).exists()
    attempts = list((tmp_path / "phase1_attempts").glob("*.json"))
    assert len(attempts) == 1
    failure = benchmark._load_self_digested(attempts[0])
    assert failure["status"] == "CEILING_EXCEEDED"
    assert failure["prior_atomic_checkpoint_preserved"] is True
    assert failure["partial_in_memory_state_resumable"] is False


def test_process_pool_transport_and_atomic_worker_persistence(tmp_path) -> None:
    full = benchmark.build_development_stream()
    tiny = benchmark.DevelopmentStream(
        rows=full.rows[:2],
        families=full.families[:2],
        training_cases=full.training_cases,
        manifest={
            **full.manifest,
            "stream_sha256": "worker-transport-only-canary",
        },
    )
    source = benchmark.build_development_source(tiny)
    cache = benchmark.build_and_validate_cache(source, tiny)
    result = benchmark.run_process_pool_transport_smoke(
        source=source,
        stream=tiny,
        cache=cache,
        path=tmp_path / "worker-smoke.json",
    )
    assert result["status"] == "PASSED"
    assert result["cache_row_count"] == 2


def test_full_development_prefix_reaches_structural_successor() -> None:
    stream = benchmark.build_development_stream()
    source = benchmark.build_development_source(stream)
    prefix_rows = tuple(
        row for row in stream.rows
        if row.region in {
            "parent_discovery",
            "parent_prospective_support_and_contradiction",
        }
    )
    observations = cache_api.build_observation_cache(
        source, prefix_rows, frame_namespace=benchmark.DEVELOPMENT_LABEL
    )
    cache = {item.row_id: item for item in observations}
    arms, discovery = benchmark._initialize_arms(
        source=source,
        stream=stream,
        cache=cache,
        seed=benchmark.development_seed(0),
    )
    assert discovery["candidate_count"] > 0
    assert discovery["shadow_parent_count"] > 0
    for row in benchmark._rows_by_region(
        stream, "parent_prospective_support_and_contradiction"
    ):
        results = [
            benchmark._plain_event(
                authority,
                row,
                cache[row.row_id],
                source_r0_digest=discovery["source_r0_digest"],
                source_continuation_digest=discovery[
                    "source_continuation_digest"
                ],
            )
            for authority in arms.values()
        ]
        assert [
            benchmark.science._semantic_trace_manifest(item["trace"])
            for item in results
        ][1:] == [
            benchmark.science._semantic_trace_manifest(item["trace"])
            for item in results
        ][:-1]
    structural = {
        mode: benchmark._structural_successor(authority)
        for mode, authority in arms.items()
    }
    assert all(benchmark._history_event_count(item) == 5 for item in arms.values())
    assert all(
        item.generation_phase.value == "PROSPECTIVE_OPEN"
        for item in arms.values()
    )
    assert structural[benchmark.SpecializationMode.DISCONNECTED][
        "sealed_request_count"
    ] == 0
