from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import shutil
from types import FunctionType, SimpleNamespace

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_process_resilient_execution_reclosure as resilience,
)


def _bindings(count: int = 6) -> tuple[dict, ...]:
    result = []
    plan = resilience.unit_plan(arms=("A", "B"), seed_count=count // 2)
    for item in plan:
        value = {
            "schema_version": "synthetic_binding.v1",
            **item,
            "source_snapshot_identity": f"snapshot-{item['unit_index']}",
            "candidate_graph_continuation_digest": (
                f"continuation-{item['unit_index']}"
            ),
            "registry_identity": f"registry-{item['arm']}",
            "expanded_package_map_digest": (
                resilience.EXPANDED_PACKAGE_MAP_DIGEST
            ),
            "row_order": ["r0", "r1"],
            "row_definition_digest": f"rows-{item['unit_index']}",
            "outcome_access": {"count": 0, "event_ids": []},
        }
        value["unit_binding_digest"] = resilience.digest(value)
        result.append(value)
    assert len(result) == count
    return tuple(result)


def _compute(binding: dict) -> dict:
    value = {
        "schema_version": "synthetic_unit.v1",
        "unit_index": binding["unit_index"],
        "unit_id": binding["unit_id"],
        "arm": binding["arm"],
        "seed_ordinal": binding["seed_ordinal"],
        "unit_binding_digest": binding["unit_binding_digest"],
        "commitments": [
            {"row_id": "r0", "value": binding["unit_index"]},
            {"row_id": "r1", "value": binding["unit_index"] + 1},
        ],
        "scan_wrapper": {
            "organism_id": binding["unit_id"],
            "qualifies": binding["unit_index"] % 2 == 0,
        },
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["unit_result_digest"] = resilience.digest(value)
    return value


def _aggregate(results: list[dict] | tuple[dict, ...]) -> dict:
    value = {
        "schema_version": "synthetic_exposure.v1",
        "ordered_unit_results": copy.deepcopy(list(results)),
        "unit_result_digests": [
            item["unit_result_digest"] for item in results
        ],
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["exposure_digest"] = resilience.digest(value)
    return value


def _execution(exposure: dict, exposure_sha256: str) -> dict:
    value = {
        "schema_version": "synthetic_execution.v1",
        "exposure_sha256": exposure_sha256,
        "exposure_digest": exposure["exposure_digest"],
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["execution_manifest_digest"] = resilience.digest(value)
    return value


def _run(
    root: Path,
    *,
    interrupt=None,
) -> dict:
    return resilience.execute_resumable_units(
        bindings=_bindings(),
        journal=resilience.ExposureUnitJournal(root),
        compute_unit=_compute,
        interrupt=interrupt,
    )


def _finalize(root: Path, results: list[dict], *, interrupt=None) -> dict:
    return resilience.finalize_exact_artifacts(
        exposure=_aggregate(results),
        build_execution=_execution,
        exposure_path=root / "exposure.json",
        execution_path=root / "execution.json",
        completion_path=root / "completion.json",
        completion_extra={"journal": "synthetic"},
        interrupt=interrupt,
    )


def _interrupt_once(stage_name: str, unit_index: int):
    state = {"raised": False}

    def value(stage: str, index: int) -> None:
        if (
            stage == stage_name
            and index == unit_index
            and not state["raised"]
        ):
            state["raised"] = True
            raise resilience.InjectedProcessInterruption(
                f"{stage}:{index}"
            )

    return value


def test_unit_plan_is_exact_A_then_B_then_C_96() -> None:
    plan = resilience.unit_plan()
    assert len(plan) == 96
    assert [row["unit_id"] for row in plan[:3]] == [
        "A/seed-00", "A/seed-01", "A/seed-02"
    ]
    assert plan[31]["unit_id"] == "A/seed-31"
    assert plan[32]["unit_id"] == "B/seed-00"
    assert plan[63]["unit_id"] == "B/seed-31"
    assert plan[64]["unit_id"] == "C/seed-00"
    assert plan[95]["unit_id"] == "C/seed-31"
    assert [row["unit_index"] for row in plan] == list(range(96))


def test_external_interruption_before_any_unit_resumes_exactly(
    tmp_path: Path,
) -> None:
    interrupt = _interrupt_once("before_unit", 0)
    with pytest.raises(resilience.InjectedProcessInterruption):
        _run(tmp_path / "journal", interrupt=interrupt)
    assert not (tmp_path / "journal").exists()
    resumed = _run(tmp_path / "journal")
    assert resumed["restart_plan"]["committed_unit_count"] == 6
    assert resumed["restart_plan"]["recomputation_count"] == 0


def test_interruption_during_unit_recomputes_and_records_attempt(
    tmp_path: Path,
) -> None:
    journal_root = tmp_path / "journal"
    with pytest.raises(resilience.InjectedProcessInterruption):
        _run(
            journal_root,
            interrupt=_interrupt_once("after_prepared", 2),
        )
    dangling = resilience.ExposureUnitJournal(journal_root).analyze(
        _bindings()
    )
    assert dangling["next_unit_index"] == 2
    assert dangling["dangling_prepared_attempt_count"] == 1
    resumed = _run(journal_root)
    assert resumed["restart_plan"]["recomputation_count"] == 1
    records = resilience.ExposureUnitJournal(journal_root).records()
    prepared = [
        row for row in records
        if row["kind"] == "PREPARED" and row["unit_index"] == 2
    ]
    assert [row["payload"]["attempt"] for row in prepared] == [1, 2]
    assert prepared[1]["payload"][
        "recomputes_prepared_record_digest"
    ] == prepared[0]["record_digest"]


def test_interruption_between_units_skips_committed_unit_after_revalidation(
    tmp_path: Path,
) -> None:
    calls = {index: 0 for index in range(6)}

    def compute(binding: dict) -> dict:
        calls[binding["unit_index"]] += 1
        return _compute(binding)

    with pytest.raises(resilience.InjectedProcessInterruption):
        resilience.execute_resumable_units(
            bindings=_bindings(),
            journal=resilience.ExposureUnitJournal(tmp_path / "journal"),
            compute_unit=compute,
            interrupt=_interrupt_once("after_committed", 0),
        )
    rows_before = resilience.ExposureUnitJournal(
        tmp_path / "journal"
    ).records()
    assert [row["kind"] for row in rows_before] == [
        "PREPARED", "COMMITTED"
    ]
    completed = resilience.execute_resumable_units(
        bindings=_bindings(),
        journal=resilience.ExposureUnitJournal(tmp_path / "journal"),
        compute_unit=compute,
    )
    rows_after = resilience.ExposureUnitJournal(
        tmp_path / "journal"
    ).records()
    assert len(rows_after) == 12
    assert completed["restart_plan"]["recomputation_count"] == 0
    assert calls[0] == 2  # initial execution plus mandatory revalidation
    assert all(calls[index] == 1 for index in range(1, 6))


def test_interrupted_and_uninterrupted_exposure_artifacts_are_byte_exact(
    tmp_path: Path,
) -> None:
    uninterrupted = _run(tmp_path / "u-journal")
    _finalize(
        tmp_path / "u-final",
        uninterrupted["unit_results"],
    )
    with pytest.raises(resilience.InjectedProcessInterruption):
        _run(
            tmp_path / "i-journal",
            interrupt=_interrupt_once("after_prepared", 3),
        )
    resumed = _run(tmp_path / "i-journal")
    _finalize(tmp_path / "i-final", resumed["unit_results"])
    for name in ("exposure.json", "execution.json"):
        assert (
            tmp_path / "u-final" / name
        ).read_bytes() == (tmp_path / "i-final" / name).read_bytes()


def test_resumable_aggregate_equals_monolithic_reference(
    tmp_path: Path,
) -> None:
    monolithic = _aggregate([_compute(item) for item in _bindings()])
    resumed = _run(tmp_path / "journal")
    journal_value = _aggregate(resumed["unit_results"])
    assert resilience.canonical_bytes(journal_value) == (
        resilience.canonical_bytes(monolithic)
    )


class _FakeCommitment:
    def __init__(self, frame_id: str) -> None:
        self.trace = SimpleNamespace(frame_id=frame_id)

    def manifest(self) -> dict:
        return {"frame_id": self.trace.frame_id}


class _FakeWrapper:
    def __init__(self, ordinal: int, arm: str) -> None:
        self.ordinal = ordinal
        self.arm = arm

    def continuation_digest(self) -> str:
        return f"continuation:{self.arm}:{self.ordinal}"

    def dumps(self) -> bytes:
        return f"payload:{self.arm}:{self.ordinal}".encode()

    def probe_real_exposure(self, frame) -> _FakeCommitment:
        return _FakeCommitment(frame.frame_id)


class _FakeRegisteredRow:
    def __init__(self, row_id: str, frame_id: str, fen: str) -> None:
        self.row_id = row_id
        self.frame_id = frame_id
        self.predecessor_fen = fen

    def manifest(self) -> dict:
        return {
            "row_id": self.row_id,
            "frame_id": self.frame_id,
            "predecessor_fen": self.predecessor_fen,
        }


class _FakeRegistry:
    def __init__(
        self,
        payloads,
        exposure_rows,
        row_order,
        run_identity,
        package_hashes,
    ) -> None:
        self.registry_id = resilience.digest([
            sorted(payloads), run_identity
        ])
        self.tape_identity = resilience.digest({
            key: [row.manifest() for row in rows]
            for key, rows in sorted(exposure_rows.items())
        })
        self.run_identity = run_identity
        self.row_order = tuple(row_order)
        self.package_hashes = dict(package_hashes)

    @classmethod
    def freeze(cls, payloads, **kwargs):
        return cls(payloads, **kwargs)

    def scan(self, organism_id, payload, commitments, **_kwargs) -> dict:
        ordinal = int(organism_id.rsplit("-", 1)[1])
        cells = {
            name: {
                "distinct_opportunities": ordinal + 4,
                "opportunity_ids": [
                    f"{name}:{ordinal}:{index}"
                    for index in range(ordinal + 4)
                ],
                "state": "MATURE",
            }
            for name in ("planted", "spurious")
        }
        return {
            "organism_id": organism_id,
            "payload": payload.decode(),
            "commitments": [item.manifest() for item in commitments],
            "scan": {"cells": cells},
        }

    def adjudicate_cohort(self, scans, **_kwargs) -> dict:
        return {
            "scan_count": len(scans),
            "scan_digest": resilience.digest(scans),
        }


class _ZeroGuard:
    @staticmethod
    def manifest() -> dict:
        return {"count": 0, "event_ids": []}


def _isolated(function, **overrides):
    namespace = dict(function.__globals__)
    namespace.update(overrides)
    clone = FunctionType(
        function.__code__,
        namespace,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    clone.__kwdefaults__ = function.__kwdefaults__
    return clone


def _small_exact_monolithic_fixture() -> tuple[dict, SimpleNamespace]:
    arms = ("A", "B", "C")
    seed_count = 2
    fen = "8/8/8/8/8/7K/5R2/7k w - - 0 1"
    rows = (
        {"phase": "suffix", "row_id": "row-0"},
        {"phase": "suffix", "row_id": "row-1"},
    )
    row_order = tuple(row["row_id"] for row in rows)
    restored = {
        (ordinal, arm): _FakeWrapper(ordinal, arm)
        for arm in arms for ordinal in range(seed_count)
    }
    prefix = {
        "results": [{
            "ordinal": ordinal,
            "targets": {
                "planted": {"cell_id": "planted"},
                "selected_spurious": {"cell_id": "spurious"},
            },
        } for ordinal in range(seed_count)],
    }
    manifest = {
        "manifest_digest": "snapshot",
        "entries": [
            {"seed_ordinal": ordinal, "arm": arm}
            for arm in arms for ordinal in range(seed_count)
        ],
    }
    ecology = {"rows": list(rows)}
    identity = {"outer_sha256": "outer"}
    receipt = {"receipt_digest": "receipt"}
    package_hashes = {"source": "0" * 64}

    def ecology_rows(value, phase):
        return tuple(row for row in value["rows"] if row["phase"] == phase)

    def registered_rows(_ecology, arm, ordinal):
        return tuple(
            _FakeRegisteredRow(
                row_id,
                f"frame:{arm}:{ordinal}:{row_id}",
                fen,
            )
            for row_id in row_order
        )

    def projection(wrapper, _pending, trace, **kwargs):
        value = {
            "row_id": kwargs["row_id"],
            "ordinal": wrapper.ordinal,
            "frame_suffix": trace.frame_id.rsplit(":", 1)[1],
        }
        value["projection_digest"] = resilience.digest(value)
        return value

    def target_counts(scan, _targets):
        return {
            "planted": copy.deepcopy(scan["cells"]["planted"]),
            "selected_spurious": copy.deepcopy(
                scan["cells"]["spurious"]
            ),
        }

    def registry_manifest(registry):
        return {
            "registry_id": registry.registry_id,
            "tape_identity": registry.tape_identity,
            "run_identity": registry.run_identity,
        }

    fake_driver = SimpleNamespace(
        EXPERIMENT_ID="synthetic-process-resilience",
        ecology_rows=ecology_rows,
        _suffix_registered_rows=registered_rows,
        classification_visible_projection=projection,
        target_cell_id=lambda targets, name: targets[name]["cell_id"],
        _target_counts_from_scan=target_counts,
        _verify_prefix_snapshot_metadata=lambda *_args: {
            "verified": True
        },
        _complete_snapshot_identity=lambda *_args: {"complete": True},
        _registry_manifest=registry_manifest,
        verify_bound_preflight_authorization=lambda **_kwargs: None,
    )
    registries = {}
    for arm in arms:
        payloads = {
            f"seed-{ordinal:02d}": restored[(ordinal, arm)].dumps()
            for ordinal in range(seed_count)
        }
        exposure_rows = {
            organism_id: registered_rows(ecology, arm, ordinal)
            for ordinal, organism_id in enumerate(payloads)
        }
        run_identity = resilience.digest({
            "experiment_id": fake_driver.EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registries[arm] = {
            "registry": _FakeRegistry.freeze(
                payloads,
                exposure_rows=exposure_rows,
                row_order=row_order,
                run_identity=run_identity,
                package_hashes=package_hashes,
            ),
            "payloads": payloads,
            "rows": exposure_rows,
            "run_identity": run_identity,
        }
    runtime = {
        "restored": restored,
        "prefix": prefix,
        "runtime_manifest": manifest,
        "identity": identity,
        "ecology": ecology,
        "receipt": receipt,
        "package_hashes": package_hashes,
        "row_order": row_order,
        "registries": registries,
    }
    helpers = SimpleNamespace(
        arms=arms,
        seed_count=seed_count,
        fake_driver=fake_driver,
        ecology_rows=ecology_rows,
        registered_rows=registered_rows,
        projection=projection,
        target_counts=target_counts,
        registry_manifest=registry_manifest,
    )
    return runtime, helpers


def test_resumable_production_assembly_equals_frozen_monolithic() -> None:
    runtime, helpers = _small_exact_monolithic_fixture()
    plan = resilience.unit_plan(
        arms=helpers.arms, seed_count=helpers.seed_count
    )
    bindings_function = _isolated(
        resilience.production_unit_bindings,
        unit_plan=lambda: plan,
    )
    compute_function = _isolated(
        resilience.compute_production_unit,
        driver=helpers.fake_driver,
    )
    assemble_function = _isolated(
        resilience.assemble_production_exposure,
        ARMS=helpers.arms,
        SEED_COUNT=helpers.seed_count,
        UNIT_COUNT=len(plan),
        MIN_TARGET_OPPORTUNITIES=4,
        MIN_QUALIFYING_SEEDS=2,
        driver=helpers.fake_driver,
    )
    bindings = bindings_function(runtime)
    resumed = assemble_function(
        runtime,
        [compute_function(binding, runtime) for binding in bindings],
    )
    monolithic_function = _isolated(
        resilience.frozen.reconstruct_exposure_value_with_expanded_map,
        ARMS=helpers.arms,
        SEED_COUNT=helpers.seed_count,
        MIN_TARGET_OPPORTUNITIES=4,
        MIN_QUALIFYING_SEEDS=2,
        EXPERIMENT_ID=helpers.fake_driver.EXPERIMENT_ID,
        V2LaboratoryRegistry=_FakeRegistry,
        validate_expanded_package_map=lambda value: dict(value),
        ecology_rows=helpers.ecology_rows,
        _suffix_registered_rows=helpers.registered_rows,
        classification_visible_projection=helpers.projection,
        target_cell_id=lambda targets, name: targets[name]["cell_id"],
        _target_counts_from_scan=helpers.target_counts,
        _registry_manifest=helpers.registry_manifest,
        _verify_prefix_snapshot_metadata=lambda *_args: {
            "verified": True
        },
        _complete_snapshot_identity=lambda *_args: {"complete": True},
        verify_bound_preflight_authorization=lambda **_kwargs: None,
        FreshScientificIntegrityError=RuntimeError,
    )
    monolithic = monolithic_function(
        identity=runtime["identity"],
        prefix=runtime["prefix"],
        ecology=runtime["ecology"],
        manifest=runtime["runtime_manifest"],
        receipt=runtime["receipt"],
        restored=runtime["restored"],
        guard=_ZeroGuard(),
        package_hashes=runtime["package_hashes"],
    )
    assert resilience.canonical_bytes(resumed) == (
        resilience.canonical_bytes(monolithic)
    )


def test_interruption_between_final_artifact_writes_recovers_exactly(
    tmp_path: Path,
) -> None:
    results = _run(tmp_path / "journal")["unit_results"]
    state = {"raised": False}

    def interrupt(stage: str) -> None:
        if stage == "after_exposure" and not state["raised"]:
            state["raised"] = True
            raise resilience.InjectedProcessInterruption(stage)

    with pytest.raises(resilience.InjectedProcessInterruption):
        _finalize(tmp_path / "final", results, interrupt=interrupt)
    assert (tmp_path / "final" / "exposure.json").is_file()
    assert not (tmp_path / "final" / "execution.json").exists()
    recovered = _finalize(tmp_path / "final", results)
    assert recovered["completion"]["exposure"]["sha256"] == (
        resilience.sha256_file(tmp_path / "final" / "exposure.json")
    )


def test_finalization_recovers_when_only_execution_file_exists(
    tmp_path: Path,
) -> None:
    results = _run(tmp_path / "journal")["unit_results"]
    _finalize(tmp_path / "source", results)
    target = tmp_path / "target"
    target.mkdir()
    shutil.copyfile(
        tmp_path / "source" / "execution.json",
        target / "execution.json",
    )
    recovered = _finalize(target, results)
    assert (target / "exposure.json").is_file()
    assert recovered["completion"]["execution_manifest"]["sha256"] == (
        resilience.sha256_file(target / "execution.json")
    )


def test_divergent_existing_final_artifact_fails_without_overwrite(
    tmp_path: Path,
) -> None:
    results = _run(tmp_path / "journal")["unit_results"]
    target = tmp_path / "final"
    target.mkdir()
    bad = b"divergent\n"
    (target / "exposure.json").write_bytes(bad)
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="divergent pre-existing exposure",
    ):
        _finalize(target, results)
    assert (target / "exposure.json").read_bytes() == bad
    assert not (target / "execution.json").exists()


def test_changed_record_is_rejected(tmp_path: Path) -> None:
    journal = resilience.ExposureUnitJournal(tmp_path / "journal")
    binding = _bindings()[0]
    journal.prepare(binding, ())
    path = next((tmp_path / "journal").glob("*.json"))
    row = json.loads(path.read_text())
    row["payload"]["unit_binding"]["unit_id"] = "foreign"
    path.write_text(json.dumps(row))
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="record digest mismatch",
    ):
        journal.analyze(_bindings())


def test_resigned_foreign_prepared_unit_is_rejected(tmp_path: Path) -> None:
    journal = resilience.ExposureUnitJournal(tmp_path / "journal")
    binding = _bindings()[0]
    journal.prepare(binding, ())
    path = next((tmp_path / "journal").glob("*.json"))
    row = json.loads(path.read_text())
    row["unit_id"] = "foreign"
    unsigned = {
        key: value for key, value in row.items()
        if key != "record_digest"
    }
    row["record_digest"] = resilience.digest(unsigned)
    path.write_text(json.dumps(row))
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="changed or foreign PREPARED",
    ):
        journal.analyze(_bindings())


def test_reordered_record_files_are_rejected(tmp_path: Path) -> None:
    _run(tmp_path / "journal")
    paths = sorted((tmp_path / "journal").glob("*.json"))
    first = paths[0].read_bytes()
    second = paths[1].read_bytes()
    paths[0].write_bytes(second)
    paths[1].write_bytes(first)
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="chain/order|filename",
    ):
        resilience.ExposureUnitJournal(
            tmp_path / "journal"
        ).analyze(_bindings())


def test_duplicate_committed_suffix_is_rejected(tmp_path: Path) -> None:
    _run(tmp_path / "journal")
    journal = resilience.ExposureUnitJournal(tmp_path / "journal")
    last = [
        row for row in journal.records() if row["kind"] == "COMMITTED"
    ][-1]
    journal.append(
        "COMMITTED",
        unit_index=5,
        unit_id="B/seed-02",
        payload=last["payload"],
    )
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="foreign exposure journal suffix",
    ):
        journal.analyze(_bindings())


def test_every_exposure_binding_result_and_record_has_zero_outcomes(
    tmp_path: Path,
) -> None:
    completed = _run(tmp_path / "journal")
    assert all(
        item["outcome_access"] == {"count": 0, "event_ids": []}
        for item in _bindings()
    )
    assert all(
        item["outcome_access"] == {"count": 0, "event_ids": []}
        for item in completed["unit_results"]
    )
    for record in resilience.ExposureUnitJournal(
        tmp_path / "journal"
    ).records():
        if record["kind"] == "PREPARED":
            assert record["payload"]["outcome_access"] == {
                "count": 0, "event_ids": []
            }
        else:
            assert record["payload"]["unit_result"]["outcome_access"] == {
                "count": 0, "event_ids": []
            }


def _append_outcome(
    journal,
    event_ids: list[str],
    event_id: str,
) -> None:
    next_ids = [*event_ids, event_id]
    journal.append(
        "OUTCOME_ACCESSED",
        seed=0,
        payload={
            "event_id": event_id,
            "transition_id": f"transition:{event_id}",
            "next_guard_manifest": {
                "count": len(next_ids),
                "event_ids": next_ids,
            },
        },
    )
    event_ids.append(event_id)


def test_journal_outcome_accounting_reports_actual_zero(tmp_path: Path) -> None:
    value = resilience.outcome_accounting_from_journal(
        tmp_path / "absent"
    )
    assert value["status"] == "known"
    assert value["count"] == 0
    assert value["event_ids"] == []
    assert value["last_valid_record_digest"] == "GENESIS"


def test_journal_outcome_accounting_reports_actual_partial_count(
    tmp_path: Path,
) -> None:
    journal = resilience.driver.DurableHashJournal(tmp_path / "journal")
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    ids: list[str] = []
    _append_outcome(journal, ids, "event-0")
    value = resilience.outcome_accounting_from_journal(
        tmp_path / "journal"
    )
    assert value["status"] == "known"
    assert value["count"] == 1
    assert value["event_ids"] == ["event-0"]


def test_journal_outcome_accounting_reports_complete_count(
    tmp_path: Path,
) -> None:
    journal = resilience.driver.DurableHashJournal(tmp_path / "journal")
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    ids: list[str] = []
    _append_outcome(journal, ids, "event-0")
    _append_outcome(journal, ids, "event-1")
    journal.append(
        "COMMITTED",
        seed=0,
        payload={"outcome_access": {"count": 2, "event_ids": ids}},
    )
    value = resilience.outcome_accounting_from_journal(
        tmp_path / "journal"
    )
    assert value["status"] == "known"
    assert value["count"] == 2
    assert value["event_ids"] == ["event-0", "event-1"]


def test_invalid_journal_reports_unknown_not_false_zero(
    tmp_path: Path,
) -> None:
    journal = resilience.driver.DurableHashJournal(tmp_path / "journal")
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    path = next((tmp_path / "journal").glob("*.json"))
    path.write_text("{}")
    value = resilience.outcome_accounting_from_journal(
        tmp_path / "journal"
    )
    assert value["status"] == "unknown"
    assert value["count"] is None
    assert value["event_ids"] is None


def test_science_failure_uses_journal_count_or_unknown(tmp_path: Path) -> None:
    started = {"science_started_digest": "started"}
    known = resilience.build_science_failure(
        RuntimeError("caught"),
        started,
        journal_path=tmp_path / "empty",
    )
    assert known["outcome_accounting"]["status"] == "known"
    assert known["outcome_accounting"]["count"] == 0
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "000000_PREPARED.json").write_text("{}")
    unknown = resilience.build_science_failure(
        RuntimeError("caught"),
        started,
        journal_path=bad,
    )
    assert unknown["outcome_accounting"]["status"] == "unknown"
    assert unknown["outcome_accounting"]["count"] is None
    assert unknown["resume_authorized"] is False


def _completed_identity() -> dict:
    return {
        "exposure": {"exposure_digest": "exposure"},
        "execution_manifest": {
            "execution_manifest_digest": "execution"
        },
        "completion": {"completion_digest": "completion"},
    }


def test_science_started_marker_retires_complete_suffix(tmp_path: Path) -> None:
    path = tmp_path / "science_started.json"
    first = resilience.persist_science_started(
        path, _completed_identity()
    )
    second = resilience.persist_science_started(
        path, _completed_identity()
    )
    assert first == second
    assert first["complete_suffix_consumed"] is True
    changed = _completed_identity()
    changed["exposure"]["exposure_digest"] = "changed"
    with pytest.raises(
        resilience.ProcessResilienceError,
        match="science-started marker changed",
    ):
        resilience.persist_science_started(path, changed)


def test_science_marker_is_written_before_environment_construction() -> None:
    source = inspect.getsource(resilience.run_science)
    assert source.index("persist_science_started") < source.index(
        "FrozenTruthfulEnvironment"
    )


def test_science_reverifies_new_package_before_committed_exposure() -> None:
    source = inspect.getsource(resilience.validate_completed_exposure)
    assert source.index("verify_package_manifests") < source.index(
        "require_committed_artifact(EXPOSURE_PATH)"
    )


def test_science_restart_rejects_FAILED_and_dangling_PREPARED(
    tmp_path: Path,
) -> None:
    failed = resilience.driver.DurableHashJournal(tmp_path / "failed")
    failed.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    failed.append(
        "FAILED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    with pytest.raises(
        resilience.ProcessResilienceError, match="FAILED"
    ):
        resilience.science_restart_plan(failed, range(2))
    dangling = resilience.driver.DurableHashJournal(tmp_path / "dangling")
    dangling.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    with pytest.raises(Exception, match="dangling PREPARED"):
        resilience.science_restart_plan(dangling, range(2))


def test_systemd_launcher_has_literal_four_element_python_argv(
    tmp_path: Path,
) -> None:
    argv = resilience.build_systemd_argv(
        "run-exposure",
        service_name="recon-v2-test",
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        wait=False,
    )
    assert argv[-4:] == resilience.build_public_command("run-exposure")
    assert argv[-4:] == (
        resilience.sys.executable,
        "-m",
        resilience.MODULE_PATH,
        "run-exposure",
    )
    assert "--" in argv
    assert not any(
        token in " ".join(argv).lower()
        for token in ("timeout=", "runtimemax", "bash -c", "nohup", "setsid", "tmux")
    )
    for key, value in resilience.deterministic_environment().items():
        assert f"--setenv={key}={value}" in argv
    assert f"--property=WorkingDirectory={resilience.ROOT}" in argv


def test_manual_persistent_command_is_exact_and_has_no_background_fallback() -> None:
    value = resilience.manual_persistent_commands("run-science")
    assert str(resilience.ROOT) in value["working_directory"]
    assert resilience.MODULE_PATH in value["command"]
    assert value["command"].endswith(" run-science")
    assert all(
        forbidden not in value["command"]
        for forbidden in ("nohup", "setsid", "tmux", "&")
    )


def test_data_free_resumption_canary_records_recomputation(
    tmp_path: Path,
) -> None:
    value = resilience.data_free_resumption_canary(tmp_path / "journal")
    assert value["unit_count"] == 4
    assert value["committed_unit_count"] == 4
    assert value["recomputation_count"] == 1
    assert value["outcome_access"] == {"count": 0, "event_ids": []}


def test_new_namespace_is_disjoint_and_old_exposure_is_never_called() -> None:
    assert resilience.PACKAGE_DIR != resilience.frozen.PACKAGE_DIR
    assert resilience.PACKAGE_ID != resilience.frozen.PACKAGE_ID
    assert resilience.EXPOSURE_PATH != resilience.frozen.EXPOSURE_PATH
    source = inspect.getsource(resilience.run_exposure)
    assert "frozen.run_exposure" not in source
    assert "stopped_adapter.run_exposure" not in source


def test_stopped_alias_package_is_verified_as_preserved_bytes() -> None:
    value = resilience.verify_stopped_alias_package_bytes()
    assert value["verification_mode"] == (
        "committed_bytes_and_frozen_digests"
    )
    assert value["readiness_digest"]
    source = inspect.getsource(resilience.verify_frozen_inputs)
    assert "frozen.verify_package_manifests" not in source


def test_source_has_no_module_global_replacement_or_forbidden_fallback() -> None:
    source = Path(resilience.__file__).read_text(encoding="utf-8")
    assert "runpy" not in source
    assert "monkeypatch" not in source
    assert "setattr(driver" not in source
    assert "setattr(frozen" not in source
    assert "nohup" not in source
    assert "setsid" not in source
    assert "tmux" not in source
