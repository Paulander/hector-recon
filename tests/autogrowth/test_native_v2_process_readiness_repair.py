from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_process_readiness_repair as repair,
)


def _binding(index: int) -> dict:
    value = {
        "unit_index": index,
        "unit_id": f"A/seed-{index:02d}",
        "arm": "A",
        "seed_ordinal": index,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["unit_binding_digest"] = repair.digest(value)
    return value


def _unit_result(binding: dict) -> dict:
    value = {
        "unit_index": binding["unit_index"],
        "unit_id": binding["unit_id"],
        "value": binding["unit_index"] * 7,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["unit_result_digest"] = repair.digest(value)
    return value


def _synthetic_exposure(_runtime, results) -> dict:
    value = {
        "schema_version": "synthetic_exposure.v1",
        "ordered_results": copy.deepcopy(list(results)),
        "admitted": True,
        "registry_package_hash": repair.EXPANDED_PACKAGE_MAP_DIGEST,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["exposure_digest"] = repair.digest(value)
    return value


def _synthetic_execution(
    _runtime,
    exposure,
    exposure_sha256,
    *,
    launch_readiness,
) -> dict:
    value = {
        "schema_version": "synthetic_execution.v1",
        "exposure_sha256": exposure_sha256,
        "exposure_digest": exposure["exposure_digest"],
        "launch_readiness_digest": launch_readiness["digest"],
        "admitted": True,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["execution_manifest_digest"] = repair.digest(value)
    return value


def _completed_exposure_fixture(
    root: Path, *, count: int = 4
) -> tuple[
    repair.RepairExposureUnitJournal,
    tuple[dict, ...],
    bytes,
    bytes,
    dict,
]:
    bindings = tuple(_binding(index) for index in range(count))
    journal = repair.RepairExposureUnitJournal(root / "journal")
    results = []
    for binding in bindings:
        prepared = journal.prepare(binding, ())
        result = _unit_result(binding)
        journal.commit(binding, prepared, result)
        results.append(result)
    exposure = _synthetic_exposure({}, results)
    exposure_bytes = repair.pretty_json_bytes(exposure)
    execution = _synthetic_execution(
        {},
        exposure,
        repair.sha256_bytes(exposure_bytes),
        launch_readiness={"digest": "launch"},
    )
    execution_bytes = repair.pretty_json_bytes(execution)
    plan = journal.analyze(bindings)
    completion = {
        "unit_count": count,
        "exposure_journal_chain_digest": plan["journal_chain_digest"],
        "exposure_recomputation_count": plan["recomputation_count"],
    }
    return (
        journal,
        bindings,
        exposure_bytes,
        execution_bytes,
        completion,
    )


def _admit_fixture(root: Path, *, count: int = 4) -> dict:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(root, count=count)
    )
    return repair.validate_exposure_journal_admission(
        runtime={},
        launch_readiness={"digest": "launch"},
        journal=journal,
        exposure_bytes=exposure,
        execution_bytes=execution,
        completion=completion,
        expected_unit_count=count,
        bindings_builder=lambda _runtime: bindings,
        exposure_builder=_synthetic_exposure,
        execution_builder=_synthetic_execution,
    )


def _resign_exposure_records(root: Path) -> None:
    previous = "GENESIS"
    for index, path in enumerate(sorted(root.glob("*.json"))):
        row = json.loads(path.read_text(encoding="utf-8"))
        row["record_index"] = index
        row["previous_record_digest"] = previous
        unsigned = {
            key: value
            for key, value in row.items()
            if key != "record_digest"
        }
        row["record_digest"] = repair.digest(unsigned)
        path.write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        previous = row["record_digest"]


def _science_rows() -> tuple[dict, ...]:
    return tuple({
        "row_id": f"suffix-{index:02d}",
        "arms": {
            arm: {"transition_id": f"{arm}:transition:{index:02d}"}
            for arm in repair.ARMS
        },
    } for index in range(repair.ROW_COUNT))


def _append_outcome(
    journal: repair.RepairDurableHashJournal,
    event_ids: list[str],
    *,
    seed: int,
    row: dict,
    arm: str,
) -> None:
    event_id = f"seed-{seed:02d}:{row['row_id']}:{arm}"
    next_ids = [*event_ids, event_id]
    journal.append(
        "OUTCOME_ACCESSED",
        seed=seed,
        payload={
            "event_id": event_id,
            "transition_id": row["arms"][arm]["transition_id"],
            "next_guard_manifest": {
                "count": len(next_ids),
                "event_ids": next_ids,
            },
        },
    )
    event_ids.append(event_id)


def _record(
    path: Path,
    *,
    key: str,
    value: dict,
) -> None:
    value[key] = repair.digest(value)
    repair.atomic_json(path, value)


def _service_status(
    *,
    terminal: bool,
    pid: str = "54321",
    code: str = "1",
    status: str = "0",
) -> dict[str, str]:
    return {
        "LoadState": "loaded",
        "ActiveState": "active" if terminal else "activating",
        "SubState": "exited" if terminal else "start",
        "Result": "success" if terminal else "success",
        "ExecMainPID": pid,
        "ExecMainCode": code if terminal else "0",
        "ExecMainStatus": status,
        "ExecMainStartTimestamp": "Tue 2026-07-28 01:00:00 CEST",
        "ExecMainExitTimestamp": (
            "Tue 2026-07-28 01:18:05 CEST" if terminal else ""
        ),
        "RuntimeMaxUSec": "infinity",
        "InvocationID": "invocation-1",
    }


def _service_attempt(root: Path, *, command: str = "service-canary") -> str:
    attempt_id = "attempt-001"
    directory = root / attempt_id
    directory.mkdir(parents=True)
    environment = repair.deterministic_environment({
        "RECON_SERVICE_CANARY_SECONDS": "1085"
    })
    python_argv = list(repair.build_public_command(command))
    launch = {
        "schema_version": "native_v2_service_attempt_launch.v1",
        "package_id": repair.PACKAGE_ID,
        "attempt_id": attempt_id,
        "command": command,
        "service_name": f"service-{attempt_id}",
        "exact_python_argv": python_argv,
        "environment": environment,
        "working_directory": str(repair.ROOT),
        "stdout_path": str(directory / "stdout.log"),
        "stderr_path": str(directory / "stderr.log"),
    }
    _record(directory / "launch.json", key="launch_digest", value=launch)
    dispatch = {
        "schema_version": "native_v2_service_attempt_dispatch.v1",
        "attempt_id": attempt_id,
        "returncode": 0,
        "stdout": "Running as unit",
        "stderr": "",
    }
    _record(
        directory / "dispatch.json",
        key="dispatch_digest",
        value=dispatch,
    )
    observation = {
        "schema_version": "native_v2_service_attempt_observation.v1",
        "attempt_id": attempt_id,
        "status": _service_status(terminal=False),
    }
    _record(
        directory / "observation.json",
        key="observation_digest",
        value=observation,
    )
    child = {
        "schema_version": "native_v2_service_canary_child.v1",
        "package_id": repair.PACKAGE_ID,
        "process_id": 54321,
        "argv": python_argv,
        "working_directory": str(repair.ROOT),
        "environment": environment,
        "requested_seconds": 1085,
        "elapsed_seconds": 1085.25,
    }
    child["canary_digest"] = repair.digest(child)
    (directory / "stdout.log").write_text(
        json.dumps(child), encoding="utf-8"
    )
    (directory / "stderr.log").write_bytes(b"")
    return attempt_id


def test_outer_package_has_separate_paths_and_literal_child_commands() -> None:
    assert repair.PACKAGE_ID not in {
        repair.previous.PACKAGE_ID,
        repair.frozen.PACKAGE_ID,
    }
    assert repair.PACKAGE_DIR != repair.previous.PACKAGE_DIR
    for command in repair.PUBLIC_CHILD_COMMANDS:
        argv = repair.build_public_command(command)
        assert len(argv) == 4
        assert argv[1:] == ("-m", repair.MODULE_PATH, command)


def test_production_runtime_uses_one_preserved_byte_verifier() -> None:
    dependencies = repair.production_runtime_dependencies()
    assert dependencies.verify_inputs is repair.verify_runtime_inputs
    source = repair.build_real_exposure_runtime.__code__.co_names
    assert "verify_package_manifests" not in source
    assert "verify_stopped_alias_package_bytes" not in source


def test_actual_runtime_call_path_calls_injected_verifier_once() -> None:
    calls = {"count": 0}

    def verify() -> dict:
        calls["count"] += 1
        return {"verified": True}

    value = repair.data_free_runtime_call_canary(verifier=verify)
    assert calls["count"] == 1
    assert value["verification_call_count"] == 1
    assert value["organism_count"] == 96
    assert value["registry_count"] == 3


def test_complete_journal_is_rebuilt_before_admission(tmp_path: Path) -> None:
    admitted = _admit_fixture(tmp_path)
    assert admitted["plan"]["committed_unit_count"] == 4
    assert admitted["plan"]["next_unit_index"] is None
    assert admitted["journal_record_count"] == 8


def test_production_sized_admission_requires_all_96_units(
    tmp_path: Path,
) -> None:
    admitted = _admit_fixture(tmp_path, count=repair.UNIT_COUNT)
    assert admitted["plan"]["committed_unit_indices"] == list(range(96))
    assert admitted["plan"]["committed_unit_count"] == 96
    assert admitted["journal_record_count"] == 192


@pytest.mark.parametrize(
    "damage",
    ("deletion", "truncation", "reordering", "replacement", "foreign"),
)
def test_journal_damage_stops_admission(
    tmp_path: Path, damage: str
) -> None:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(tmp_path)
    )
    paths = sorted(journal.root.glob("*.json"))
    if damage == "deletion":
        paths[2].unlink()
    elif damage == "truncation":
        paths[-1].unlink()
    elif damage == "reordering":
        first, second = paths[0].read_bytes(), paths[1].read_bytes()
        paths[0].write_bytes(second)
        paths[1].write_bytes(first)
    elif damage == "replacement":
        row = json.loads(paths[-1].read_text(encoding="utf-8"))
        row["unit_id"] = "foreign"
        paths[-1].write_text(json.dumps(row), encoding="utf-8")
        _resign_exposure_records(journal.root)
    else:
        journal.append(
            "COMMITTED",
            unit_index=3,
            unit_id=bindings[-1]["unit_id"],
            payload={
                "unit_binding_digest": bindings[-1][
                    "unit_binding_digest"
                ],
                "prepared_record_digest": "foreign",
                "unit_result": _unit_result(bindings[-1]),
                "unit_result_digest": "foreign",
            },
        )
    with pytest.raises(Exception):
        repair.validate_exposure_journal_admission(
            runtime={},
            launch_readiness={"digest": "launch"},
            journal=journal,
            exposure_bytes=exposure,
            execution_bytes=execution,
            completion=completion,
            expected_unit_count=4,
            bindings_builder=lambda _runtime: bindings,
            exposure_builder=_synthetic_exposure,
            execution_builder=_synthetic_execution,
        )


def test_unfinished_preparation_stops_admission(tmp_path: Path) -> None:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(tmp_path, count=3)
    )
    extra = _binding(3)
    journal.prepare(extra, ())
    with pytest.raises(Exception):
        repair.validate_exposure_journal_admission(
            runtime={},
            launch_readiness={"digest": "launch"},
            journal=journal,
            exposure_bytes=exposure,
            execution_bytes=execution,
            completion=completion,
            expected_unit_count=4,
            bindings_builder=lambda _runtime: (*bindings, extra),
            exposure_builder=_synthetic_exposure,
            execution_builder=_synthetic_execution,
        )


@pytest.mark.parametrize(
    "field",
    (
        "exposure_journal_chain_digest",
        "unit_count",
        "exposure_recomputation_count",
    ),
)
def test_completion_marker_must_match_journal(
    tmp_path: Path, field: str
) -> None:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(tmp_path)
    )
    completion[field] = "changed"
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="completion/journal",
    ):
        repair.validate_exposure_journal_admission(
            runtime={},
            launch_readiness={"digest": "launch"},
            journal=journal,
            exposure_bytes=exposure,
            execution_bytes=execution,
            completion=completion,
            expected_unit_count=4,
            bindings_builder=lambda _runtime: bindings,
            exposure_builder=_synthetic_exposure,
            execution_builder=_synthetic_execution,
        )


def test_rebuilt_values_must_be_byte_identical(tmp_path: Path) -> None:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(tmp_path)
    )
    changed = json.loads(exposure)
    changed["extra"] = True
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="differs from journal reconstruction",
    ):
        repair.validate_exposure_journal_admission(
            runtime={},
            launch_readiness={"digest": "launch"},
            journal=journal,
            exposure_bytes=repair.pretty_json_bytes(changed),
            execution_bytes=execution,
            completion=completion,
            expected_unit_count=4,
            bindings_builder=lambda _runtime: bindings,
            exposure_builder=_synthetic_exposure,
            execution_builder=_synthetic_execution,
        )


def test_resigned_journal_alteration_still_fails_artifact_comparison(
    tmp_path: Path,
) -> None:
    journal, bindings, exposure, execution, completion = (
        _completed_exposure_fixture(tmp_path)
    )
    path = sorted(journal.root.glob("*.json"))[-1]
    row = json.loads(path.read_text(encoding="utf-8"))
    row["payload"]["unit_result"]["value"] = 999
    row["payload"]["unit_result_digest"] = repair.digest(
        row["payload"]["unit_result"]
    )
    path.write_text(json.dumps(row), encoding="utf-8")
    _resign_exposure_records(journal.root)
    changed_plan = journal.analyze(bindings)
    completion["exposure_journal_chain_digest"] = changed_plan[
        "journal_chain_digest"
    ]
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="differs from journal reconstruction",
    ):
        repair.validate_exposure_journal_admission(
            runtime={},
            launch_readiness={"digest": "launch"},
            journal=journal,
            exposure_bytes=exposure,
            execution_bytes=execution,
            completion=completion,
            expected_unit_count=4,
            bindings_builder=lambda _runtime: bindings,
            exposure_builder=_synthetic_exposure,
            execution_builder=_synthetic_execution,
        )


def _completed_identity() -> dict:
    return {
        "exposure": {"exposure_digest": "exposure"},
        "execution_manifest": {
            "execution_manifest_digest": "execution"
        },
        "completion": {"completion_digest": "completion"},
    }


@pytest.mark.parametrize(
    "field",
    (
        "schema_version",
        "package_id",
        "experiment_id",
        "complete_suffix_consumed",
        "cohort_digest",
        "expanded_package_map_digest",
        "exposure_digest",
        "execution_manifest_digest",
        "exposure_completion_digest",
    ),
)
def test_existing_science_marker_requires_complete_identity(
    tmp_path: Path, field: str
) -> None:
    path = tmp_path / "science_started.json"
    repair.persist_science_started(path, _completed_identity())
    value = json.loads(path.read_text(encoding="utf-8"))
    value[field] = "changed"
    value["science_started_digest"] = repair.digest({
        key: item
        for key, item in value.items()
        if key != "science_started_digest"
    })
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match=f"science-started marker changed:{field}",
    ):
        repair.persist_science_started(path, _completed_identity())


def test_partial_outcome_count_requires_canonical_interactions(
    tmp_path: Path,
) -> None:
    rows = _science_rows()
    journal = repair.RepairDurableHashJournal(tmp_path / "science")
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    ids: list[str] = []
    for arm in repair.ARMS:
        _append_outcome(
            journal, ids, seed=0, row=rows[0], arm=arm
        )
    journal.append(
        "TRI_ARM_ROW_COMMITTED",
        seed=0,
        payload={
            "row_id": rows[0]["row_id"],
            "outcome_access": {
                "count": len(ids),
                "event_ids": ids,
            },
        },
    )
    value = repair.outcome_accounting_from_journal(
        journal.root, expected_rows=rows
    )
    assert value["status"] == "known"
    assert value["count"] == 3
    assert value["event_ids"] == ids


@pytest.mark.parametrize(
    ("field", "changed"),
    (
        ("event_id", "foreign"),
        ("transition_id", "foreign"),
        ("next_guard_manifest", {"count": 0, "event_ids": []}),
    ),
)
def test_semantically_changed_partial_count_is_unknown(
    tmp_path: Path, field: str, changed
) -> None:
    rows = _science_rows()
    journal = repair.RepairDurableHashJournal(tmp_path / field)
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    ids: list[str] = []
    _append_outcome(
        journal, ids, seed=0, row=rows[0], arm=repair.ARMS[0]
    )
    path = sorted(journal.root.glob("*.json"))[-1]
    row = json.loads(path.read_text(encoding="utf-8"))
    row["payload"][field] = changed
    unsigned = {
        key: item for key, item in row.items() if key != "record_hash"
    }
    row["record_hash"] = repair.digest(unsigned)
    path.write_text(json.dumps(row), encoding="utf-8")
    value = repair.outcome_accounting_from_journal(
        journal.root, expected_rows=rows
    )
    assert value["status"] == "unknown"
    assert value["count"] is None
    assert value["event_ids"] is None


def test_valid_failure_checkpoint_retains_only_validated_count(
    tmp_path: Path,
) -> None:
    rows = _science_rows()
    journal = repair.RepairDurableHashJournal(tmp_path / "failure")
    journal.append(
        "PREPARED",
        seed=0,
        payload={"outcome_access": {"count": 0, "event_ids": []}},
    )
    ids: list[str] = []
    _append_outcome(
        journal, ids, seed=0, row=rows[0], arm=repair.ARMS[0]
    )
    journal.append(
        "FAILED",
        seed=0,
        payload={
            "detail": "synthetic",
            "outcome_access": {"count": 1, "event_ids": ids},
        },
    )
    value = repair.outcome_accounting_from_journal(
        journal.root, expected_rows=rows
    )
    assert value["status"] == "known"
    assert value["count"] == 1
    assert value["canonical_prefix"]["failed"] is True


def test_invalid_hash_reports_unknown_not_zero(tmp_path: Path) -> None:
    rows = _science_rows()
    root = tmp_path / "bad"
    root.mkdir()
    (root / "000000_PREPARED.json").write_text("{}", encoding="utf-8")
    value = repair.outcome_accounting_from_journal(
        root, expected_rows=rows
    )
    assert value["status"] == "unknown"
    assert value["count"] is None


def test_atomic_interruption_recovers_only_exact_bytes(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    payload = b"{\"safe\":true}\n"

    def interrupt(_path: Path) -> None:
        raise repair.InjectedAtomicInterruption

    with pytest.raises(repair.InjectedAtomicInterruption):
        repair.atomic_bytes(
            path, payload, after_fsync=interrupt
        )
    temporary = repair.atomic_temporary_path(path)
    assert temporary.read_bytes() == payload
    assert not path.exists()
    repair.atomic_bytes(path, payload)
    assert path.read_bytes() == payload
    assert not temporary.exists()


def test_atomic_interruption_with_changed_bytes_stops(tmp_path: Path) -> None:
    path = tmp_path / "result.json"

    def interrupt(_path: Path) -> None:
        raise repair.InjectedAtomicInterruption

    with pytest.raises(repair.InjectedAtomicInterruption):
        repair.atomic_bytes(
            path, b"first", after_fsync=interrupt
        )
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="interrupted atomic temporary",
    ):
        repair.atomic_bytes(path, b"second")
    assert repair.atomic_temporary_path(path).read_bytes() == b"first"
    assert not path.exists()


def test_atomic_target_plus_temporary_stops_without_changes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "result.json"
    temporary = repair.atomic_temporary_path(path)
    path.write_bytes(b"same")
    temporary.write_bytes(b"same")
    before = (path.read_bytes(), temporary.read_bytes())
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="target and temporary both exist",
    ):
        repair.atomic_bytes(path, b"same")
    assert (path.read_bytes(), temporary.read_bytes()) == before


def test_only_precisely_named_package_temporaries_are_recognized() -> None:
    target = repair.ROOT / repair.READINESS_PATH
    assert repair.is_recognized_package_temporary(
        repair.atomic_temporary_path(target)
    )
    assert not repair.is_recognized_package_temporary(
        target.parent / ".unrelated.tmp"
    )


def test_service_argv_is_unique_file_backed_and_has_no_timeout(
    tmp_path: Path,
) -> None:
    argv = repair.build_service_argv(
        command="service-canary",
        service_name="unique-service",
        stdout_path=tmp_path / "one.stdout",
        stderr_path=tmp_path / "one.stderr",
        environment={"LC_ALL": "C"},
    )
    joined = "\n".join(argv)
    assert "--unit=unique-service" in argv
    assert f"--property=StandardOutput=file:{tmp_path / 'one.stdout'}" in argv
    assert f"--property=StandardError=file:{tmp_path / 'one.stderr'}" in argv
    assert "RuntimeMax" not in joined
    assert "/bin/sh" not in joined
    assert tuple(argv[-4:]) == repair.build_public_command(
        "service-canary"
    )


def test_service_poll_records_terminal_process_and_logs(tmp_path: Path) -> None:
    attempt_id = _service_attempt(tmp_path)
    final = repair.poll_service_attempt(
        attempt_id,
        persist_canary_record=False,
        attempt_root=tmp_path,
        status_reader=lambda _name: _service_status(
            terminal=True, pid="0"
        ),
    )
    assert final["terminal"] is True
    assert final["process_id"] == 54321
    assert final["terminal_status"]["exit_status"] == 0
    assert final["terminal_status"]["signal_status"] is None
    assert final["terminal_status"]["runtime_max_usec"] == "infinity"
    assert final["stdout_log"]["size"] > 0
    assert len(final["stdout_log"]["sha256"]) == 64
    assert final["stderr_log"]["size"] == 0
    again = repair.poll_service_attempt(
        attempt_id,
        persist_canary_record=False,
        attempt_root=tmp_path,
        status_reader=lambda _name: (_ for _ in ()).throw(
            AssertionError("terminal attempt must not be repolled")
        ),
    )
    assert again == final


def test_service_poll_records_signal_separately(tmp_path: Path) -> None:
    attempt_id = _service_attempt(tmp_path)
    final = repair.poll_service_attempt(
        attempt_id,
        persist_canary_record=False,
        attempt_root=tmp_path,
        status_reader=lambda _name: _service_status(
            terminal=True, code="2", status="15"
        ),
    )
    assert final["terminal_status"]["exit_status"] is None
    assert final["terminal_status"]["signal_status"] == 15


def test_concurrent_matching_service_is_rejected(tmp_path: Path) -> None:
    _service_attempt(tmp_path)
    with pytest.raises(
        repair.ProcessReadinessRepairError,
        match="concurrent matching service",
    ):
        repair.reject_concurrent_matching_run(
            "service-canary",
            attempt_root=tmp_path,
            status_reader=lambda _name: _service_status(terminal=False),
        )


def test_different_service_command_does_not_conflict(tmp_path: Path) -> None:
    _service_attempt(tmp_path, command="service-canary")
    repair.reject_concurrent_matching_run(
        "run-exposure",
        attempt_root=tmp_path,
        status_reader=lambda _name: (_ for _ in ()).throw(
            AssertionError("different commands do not query status")
        ),
    )


def test_protected_prior_paths_do_not_overlap_repair_outputs() -> None:
    repair_paths = {
        repair.SOURCE_MANIFEST_PATH,
        repair.ARTIFACT_BINDING_PATH,
        repair.LAUNCH_READINESS_PATH,
        repair.SERVICE_CANARY_RECORD_PATH,
        repair.READINESS_PATH,
        repair.EXPOSURE_PATH,
        repair.EXECUTION_MANIFEST_PATH,
        repair.EXPOSURE_COMPLETION_PATH,
        repair.SCIENCE_STARTED_PATH,
        repair.RESULT_PATH,
    }
    previous_paths = {
        repair.previous.SOURCE_MANIFEST_PATH,
        repair.previous.ARTIFACT_BINDING_PATH,
        repair.previous.READINESS_PATH,
        repair.previous.EXPOSURE_PATH,
        repair.previous.EXECUTION_MANIFEST_PATH,
        repair.previous.EXPOSURE_COMPLETION_PATH,
        repair.previous.SCIENCE_STARTED_PATH,
        repair.previous.RESULT_PATH,
    }
    assert repair_paths.isdisjoint(previous_paths)
