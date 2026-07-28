from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_execution_launch_amendment as amendment,
)


ATTEMPT_1 = (
    "20260728T120000000000Z-"
    "11111111111111111111111111111111"
)
ATTEMPT_2 = (
    "20260728T120001000000Z-"
    "22222222222222222222222222222222"
)


def _completed(
    argv=(), returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        list(argv), returncode, stdout, stderr
    )


def _status(
    *,
    terminal: bool,
    pid: str = "4242",
    code: str = "1",
    result: str = "success",
    status: str = "0",
) -> dict[str, str]:
    return {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "exited" if terminal else "running",
        "Result": result,
        "ExecMainPID": pid,
        "ExecMainCode": code if terminal else "0",
        "ExecMainStatus": status,
        "ExecMainStartTimestamp": "Tue 2026-07-28 12:00:00 CEST",
        "ExecMainExitTimestamp": (
            "Tue 2026-07-28 12:18:05 CEST" if terminal else ""
        ),
        "RuntimeMaxUSec": "infinity",
        "InvocationID": "invocation-1",
    }


def _unloaded_status() -> dict[str, str]:
    return {
        **_status(terminal=True, pid="0"),
        "LoadState": "not-found",
        "ActiveState": "inactive",
        "SubState": "dead",
    }


def _readiness_identity(kind: str = "final_readiness") -> dict:
    return {
        "kind": kind,
        "path": (
            amendment.READINESS_PATH.as_posix()
            if kind == "final_readiness"
            else amendment.LAUNCH_READINESS_PATH.as_posix()
        ),
        "sha256": f"{kind}-sha",
        "digest": f"{kind}-digest",
    }


def _launch(
    tmp_path: Path,
    *,
    command: str = "run-exposure",
    attempt_id: str = ATTEMPT_1,
    worktree_rows: tuple[str, ...] = (),
) -> dict:
    readiness = _readiness_identity(
        "launch_readiness"
        if command == "service-canary"
        else "final_readiness"
    )
    return amendment.launch_service_attempt(
        command,
        canary_seconds=1 if command == "service-canary" else None,
        attempt_root=tmp_path / "attempts",
        lock_root=tmp_path / "locks",
        attempt_id_factory=lambda: attempt_id,
        worktree_validator=lambda _command: (
            amendment.validate_production_worktree_rows(worktree_rows)
            if command != "service-canary"
            else {
                "row_count": 0,
                "rows": [],
                "allowed": True,
                "worktree_digest": "clean",
            }
        ),
        package_verifier=lambda: {"package": "frozen"},
        readiness_identity=readiness,
        status_reader=lambda _name: _status(terminal=False),
        dispatch_runner=lambda argv: _completed(
            argv, stdout="Running as unit"
        ),
        exact_head="frozen-head",
    )


def _attempt_dir(tmp_path: Path, attempt_id: str = ATTEMPT_1) -> Path:
    return tmp_path / "attempts" / attempt_id


def _write_child_result(
    directory: Path,
    *,
    command: str,
) -> dict:
    launch = amendment.load_json(directory / "launch.json")
    value = {
        "schema_version": "synthetic_child.v1",
        "package_id": amendment.PACKAGE_ID,
        "command": command,
        "attempt_id": launch["attempt_id"],
        "launch_digest": launch["launch_digest"],
        "requested_seconds": 1085,
        "elapsed_seconds": 1085.25,
    }
    value["child_result_digest"] = amendment.digest(value)
    (directory / "stdout.log").write_text(
        json.dumps(value), encoding="utf-8"
    )
    (directory / "stderr.log").write_bytes(b"")
    return value


def _finalize_external_attempt(directory: Path) -> None:
    value = {
        "schema_version": "synthetic_final.v1",
        "package_id": amendment.PACKAGE_ID,
        "attempt_id": directory.name,
    }
    value["final_record_digest"] = amendment.digest(value)
    amendment.atomic_json(directory / "final.json", value)


def test_package_and_paths_are_separate_from_pre_review() -> None:
    assert amendment.PACKAGE_ID != amendment.prior.PACKAGE_ID
    assert amendment.PACKAGE_DIR != amendment.prior.PACKAGE_DIR
    assert amendment.READINESS_PATH != amendment.prior.READINESS_PATH
    assert amendment.SOURCE_MANIFEST_PATH != (
        amendment.prior.SOURCE_MANIFEST_PATH
    )


def test_public_child_commands_are_literal_four_item_python_commands() -> None:
    for command in amendment.PUBLIC_CHILD_COMMANDS:
        argv = amendment.build_public_command(command)
        assert len(argv) == 4
        assert argv[1:] == ("-m", amendment.MODULE_PATH, command)


def test_service_argv_has_no_shell_or_wall_limit(tmp_path: Path) -> None:
    child = amendment.build_public_command("run-exposure")
    argv = amendment.build_service_argv(
        service_name="unique",
        stdout_path=tmp_path / "stdout",
        stderr_path=tmp_path / "stderr",
        environment={"LC_ALL": "C.UTF-8"},
        child_command=child,
    )
    text = "\n".join(argv)
    assert tuple(argv[-4:]) == child
    assert "--unit=unique" in argv
    assert "RuntimeMax" not in text
    assert "/bin/sh" not in text


def _expected_final() -> dict:
    return {
        "schema_version": "native_v2_execution_launch_final.v1",
        "package_id": amendment.PACKAGE_ID,
        "source_manifest": {"sha256": "s", "digest": "sd"},
        "artifact_binding": {"sha256": "a", "digest": "ad"},
        "launch_readiness": {"sha256": "l", "digest": "ld"},
        "service_canary": {
            "path": "canary",
            "sha256": "c",
            "size": 1,
            "digest": "cd",
            "attempt_id": ATTEMPT_1,
            "elapsed_seconds": 1085.1,
        },
        "pre_review_readiness": {"sha256": "p", "digest": "pd"},
        "cohort_digest": amendment.ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": (
            amendment.EXPANDED_PACKAGE_MAP_DIGEST
        ),
        "production_launch_authorized": True,
        "real_exposure_run": False,
        "real_outcome_run": False,
        "outcome_access": {"count": 0, "event_ids": []},
        "stop_before_exposure": True,
    }


@pytest.mark.parametrize(
    "field",
    (
        "schema_version",
        "package_id",
        "source_manifest",
        "artifact_binding",
        "launch_readiness",
        "service_canary",
        "pre_review_readiness",
        "cohort_digest",
        "expanded_package_map_digest",
        "production_launch_authorized",
        "real_exposure_run",
        "real_outcome_run",
        "outcome_access",
        "stop_before_exposure",
    ),
)
def test_complete_final_readiness_identity_rejects_each_changed_field(
    field: str,
) -> None:
    expected = _expected_final()
    value = copy.deepcopy(expected)
    value[field] = "changed"
    value["readiness_digest"] = amendment.digest(value)
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="final readiness identity changed",
    ):
        amendment.validate_final_readiness_identity(value, expected)


def test_complete_final_readiness_rejects_extra_field() -> None:
    expected = _expected_final()
    value = {**expected, "extra": True}
    value["readiness_digest"] = amendment.digest(value)
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="field set changed",
    ):
        amendment.validate_final_readiness_identity(value, expected)


def test_production_worktree_allows_exact_partial_exposure_journal() -> None:
    journal = amendment.prior.EXPOSURE_JOURNAL_DIR.as_posix()
    rows = (
        f"?? {journal}/",
        (
            "?? "
            f"{journal}/000000_PREPARED_000_A_seed-00.json"
        ),
    )
    value = amendment.validate_production_worktree_rows(rows)
    assert value["allowed"] is True
    assert value["row_count"] == 2


@pytest.mark.parametrize(
    "row",
    (
        "?? unrelated.txt",
        (
            "?? "
            + amendment.prior.EXPOSURE_PATH.as_posix()
            + ".foreign"
        ),
        (
            "?? "
            + amendment.prior.EXPOSURE_JOURNAL_DIR.as_posix()
            + "-foreign/"
        ),
    ),
)
def test_production_worktree_rejects_every_unrelated_path(row: str) -> None:
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="unexpected production worktree",
    ):
        amendment.validate_production_worktree_rows((row,))


def test_production_worktree_uses_inherited_exact_deep_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        amendment,
        "_git",
        lambda *_args: (
            "?? "
            + amendment.prior.EXPOSURE_JOURNAL_DIR.as_posix()
            + "/"
        ),
    )
    monkeypatch.setattr(
        amendment.prior,
        "_require_clean_worktree",
        lambda *, allow_runtime: calls.append(allow_runtime),
    )
    value = amendment.require_launch_worktree("run-exposure")
    assert value["allowed"] is True
    assert calls == [True]


def test_valid_partial_exposure_can_relaunch_with_new_attempt_id(
    tmp_path: Path,
) -> None:
    journal = amendment.prior.EXPOSURE_JOURNAL_DIR.as_posix()
    rows = (f"?? {journal}/",)
    first = _launch(
        tmp_path, attempt_id=ATTEMPT_1, worktree_rows=rows
    )
    _finalize_external_attempt(_attempt_dir(tmp_path, ATTEMPT_1))
    second = _launch(
        tmp_path, attempt_id=ATTEMPT_2, worktree_rows=rows
    )
    assert first["attempt_id"] == ATTEMPT_1
    assert second["attempt_id"] == ATTEMPT_2
    assert first["launch_digest"] != second["launch_digest"]
    assert (_attempt_dir(tmp_path, ATTEMPT_1) / "launch.json").is_file()
    assert (_attempt_dir(tmp_path, ATTEMPT_2) / "launch.json").is_file()


def test_atomic_launch_lock_closes_simultaneous_launcher_race(
    tmp_path: Path,
) -> None:
    with amendment.acquire_launch_lock(
        "run-exposure", lock_root=tmp_path, owner="one"
    ):
        with pytest.raises(
            amendment.ExecutionLaunchAmendmentError,
            match="lock already exists",
        ):
            with amendment.acquire_launch_lock(
                "run-exposure", lock_root=tmp_path, owner="two"
            ):
                raise AssertionError("unreachable")
    assert not (tmp_path / "run-exposure.lock").exists()


def test_corrupt_final_attempt_cannot_authorize_relaunch(
    tmp_path: Path,
) -> None:
    _launch(tmp_path)
    (_attempt_dir(tmp_path) / "final.json").write_text(
        "{}", encoding="utf-8"
    )
    with pytest.raises(Exception, match="self-digest"):
        _launch(tmp_path, attempt_id=ATTEMPT_2)


def test_valid_orphaned_terminal_cleanup_allows_new_attempt(
    tmp_path: Path,
) -> None:
    _launch(tmp_path)
    directory = _attempt_dir(tmp_path)
    launch = amendment.load_json(directory / "launch.json")
    terminal = {
        "schema_version": "native_v2_terminal_capture.v1",
        "package_id": amendment.PACKAGE_ID,
        "attempt_id": ATTEMPT_1,
        "command": "run-exposure",
        "terminal_status": {"exec_main_code": "1"},
    }
    terminal["terminal_capture_digest"] = amendment.digest(terminal)
    amendment.atomic_json(directory / "terminal.json", terminal)
    service_name = launch["service_name"]
    actions = [
        {
            "action": "stop",
            "argv": ["systemctl", "--user", "stop", service_name],
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        },
        {
            "action": "reset-failed",
            "argv": [
                "systemctl", "--user", "reset-failed", service_name
            ],
            "returncode": 1,
            "stdout": "",
            "stderr": (
                "Failed to reset failed state of unit "
                f"{service_name}.service: Unit "
                f"{service_name}.service not loaded.\n"
            ),
        },
    ]
    cleanup = {
        "schema_version": "native_v2_service_cleanup.v1",
        "package_id": amendment.PACKAGE_ID,
        "service_name": service_name,
        "actions": actions,
        "completed": False,
    }
    cleanup["cleanup_digest"] = amendment.digest(cleanup)
    amendment.atomic_json(directory / "cleanup.json", cleanup)
    amendment.reject_concurrent_matching_run(
        "run-exposure",
        attempt_root=tmp_path / "attempts",
        status_reader=lambda _name: _unloaded_status(),
    )


def test_malformed_orphaned_cleanup_still_blocks_relaunch(
    tmp_path: Path,
) -> None:
    _launch(tmp_path)
    directory = _attempt_dir(tmp_path)
    terminal = {
        "attempt_id": ATTEMPT_1,
        "command": "run-exposure",
        "terminal_status": {"exec_main_code": "1"},
    }
    terminal["terminal_capture_digest"] = amendment.digest(terminal)
    amendment.atomic_json(directory / "terminal.json", terminal)
    cleanup = {
        "actions": [{
            "action": "stop",
            "argv": ["systemctl", "--user", "stop", "wrong"],
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }],
        "completed": False,
    }
    cleanup["cleanup_digest"] = amendment.digest(cleanup)
    amendment.atomic_json(directory / "cleanup.json", cleanup)
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="matching service",
    ):
        amendment.reject_concurrent_matching_run(
            "run-exposure",
            attempt_root=tmp_path / "attempts",
            status_reader=lambda _name: _unloaded_status(),
        )


def test_launch_record_binds_final_readiness_and_context(
    tmp_path: Path,
) -> None:
    launched = _launch(tmp_path)
    record = amendment.load_json(
        _attempt_dir(tmp_path) / "launch.json"
    )
    assert record["identity"]["readiness"] == _readiness_identity()
    assert record["child_context"][amendment.CONTEXT_ATTEMPT] == (
        ATTEMPT_1
    )
    assert record["child_context"][amendment.CONTEXT_DIGEST] == (
        launched["launch_digest"]
    )
    assert record["identity"]["exact_python_argv"] == list(
        amendment.build_public_command("run-exposure")
    )
    assert record["identity"]["exact_head"] == "frozen-head"


def test_production_launcher_calls_final_readiness_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(
        amendment,
        "sha256_file",
        lambda path: (
            "final-sha"
            if path == amendment.ROOT / amendment.READINESS_PATH
            else (_ for _ in ()).throw(
                AssertionError(f"unexpected hash path:{path}")
            )
        ),
    )
    amendment.launch_service_attempt(
        "run-exposure",
        attempt_root=tmp_path / "attempts",
        lock_root=tmp_path / "locks",
        attempt_id_factory=lambda: ATTEMPT_1,
        worktree_validator=lambda _command: {"allowed": True},
        package_verifier=lambda: {"package": "frozen"},
        final_readiness_loader=lambda **_kwargs: (
            calls.append("final")
            or {"readiness_digest": "final-digest"}
        ),
        launch_readiness_loader=lambda **_kwargs: (
            (_ for _ in ()).throw(
                AssertionError("production cannot use launch readiness")
            )
        ),
        status_reader=lambda _name: _status(terminal=False),
        dispatch_runner=lambda argv: _completed(argv),
        exact_head="frozen-head",
    )
    assert calls == ["final"]
    launch = amendment.load_json(
        _attempt_dir(tmp_path) / "launch.json"
    )
    assert launch["identity"]["readiness"] == {
        "kind": "final_readiness",
        "path": amendment.READINESS_PATH.as_posix(),
        "sha256": "final-sha",
        "digest": "final-digest",
    }


def test_recorded_launch_context_validates_exact_record(tmp_path: Path) -> None:
    _launch(tmp_path)
    launch = amendment.load_json(
        _attempt_dir(tmp_path) / "launch.json"
    )
    value = amendment.validate_launch_context(
        "run-exposure",
        environment=launch["environment"],
        attempt_root=tmp_path / "attempts",
        readiness_identity=_readiness_identity(),
        package_identity={"package": "frozen"},
        expected_head="frozen-head",
    )
    assert value["attempt_id"] == ATTEMPT_1
    assert value["launch_digest"] == launch["launch_digest"]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        (amendment.CONTEXT_ATTEMPT, ATTEMPT_2),
        (amendment.CONTEXT_COMMAND, "run-science"),
        (amendment.CONTEXT_DIGEST, "changed"),
        (amendment.CONTEXT_READINESS_SHA, "changed"),
        (amendment.CONTEXT_READINESS_DIGEST, "changed"),
    ),
)
def test_recorded_launch_context_rejects_tampering(
    tmp_path: Path, field: str, value: str
) -> None:
    _launch(tmp_path)
    launch = amendment.load_json(
        _attempt_dir(tmp_path) / "launch.json"
    )
    environment = dict(launch["environment"])
    environment[field] = value
    with pytest.raises(amendment.ExecutionLaunchAmendmentError):
        amendment.validate_launch_context(
            "run-exposure",
            environment=environment,
            attempt_root=tmp_path / "attempts",
            readiness_identity=_readiness_identity(),
            package_identity={"package": "frozen"},
            expected_head="frozen-head",
        )


@pytest.mark.parametrize(
    "field",
    ("exact_head", "exact_python_argv", "base_environment"),
)
def test_recorded_launch_context_rejects_changed_launch_identity(
    tmp_path: Path, field: str
) -> None:
    _launch(tmp_path)
    path = _attempt_dir(tmp_path) / "launch.json"
    launch = amendment.load_json(path)
    launch["identity"][field] = "changed"
    launch["launch_digest"] = amendment.digest(launch["identity"])
    launch["child_context"][amendment.CONTEXT_DIGEST] = (
        launch["launch_digest"]
    )
    launch["environment"][amendment.CONTEXT_DIGEST] = (
        launch["launch_digest"]
    )
    launch["systemd_argv"] = list(amendment.build_service_argv(
        service_name=launch["service_name"],
        stdout_path=Path(launch["identity"]["stdout_path"]),
        stderr_path=Path(launch["identity"]["stderr_path"]),
        environment=launch["environment"],
        child_command=amendment.build_public_command("run-exposure"),
    ))
    launch.pop("launch_record_digest")
    launch["launch_record_digest"] = amendment.digest(launch)
    path.write_bytes(amendment.pretty_json_bytes(launch))
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="recorded launch context identity changed",
    ):
        amendment.validate_launch_context(
            "run-exposure",
            environment=launch["environment"],
            attempt_root=tmp_path / "attempts",
            readiness_identity=_readiness_identity(),
            package_identity={"package": "frozen"},
            expected_head="frozen-head",
        )


def test_manual_production_child_stops_before_delegate() -> None:
    calls = []
    deps = amendment.ChildDependencies(
        entry_gate=lambda: calls.append("entry") or {},
        readiness_loader=lambda **_kwargs: (
            calls.append("readiness") or {}
        ),
        context_validator=lambda _command: (
            amendment.validate_launch_context(
                "run-exposure", environment={}
            )
        ),
        worktree_validator=lambda _command: (
            calls.append("worktree") or {}
        ),
        exposure_admission=lambda: {},
        exposure_delegate=lambda: calls.append("delegate") or {},
        science_delegate=lambda: {},
    )
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="context is absent",
    ):
        amendment.run_exposure_child(deps)
    assert calls == ["entry", "readiness"]


def test_exposure_child_gate_order_includes_final_readiness() -> None:
    calls = []
    context = {
        "attempt_id": ATTEMPT_1,
        "launch_digest": "launch",
        "readiness": _readiness_identity(),
    }
    deps = amendment.ChildDependencies(
        entry_gate=lambda: calls.append("entry") or {},
        readiness_loader=lambda **_kwargs: (
            calls.append("readiness") or {}
        ),
        context_validator=lambda _command: (
            calls.append("context") or context
        ),
        worktree_validator=lambda _command: (
            calls.append("worktree") or {}
        ),
        exposure_admission=lambda: {},
        exposure_delegate=lambda: calls.append("delegate") or {"ok": True},
        science_delegate=lambda: {},
    )
    value = amendment.run_exposure_child(deps)
    assert calls == [
        "entry", "readiness", "context", "worktree", "delegate"
    ]
    assert value["final_readiness"] == _readiness_identity()


def test_science_admission_begins_with_final_readiness() -> None:
    calls = []
    completed = {
        "exposure": {"exposure_digest": "e"},
        "execution_manifest": {
            "execution_manifest_digest": "x"
        },
        "completion": {"completion_digest": "c"},
    }
    value = amendment.validate_science_admission(
        readiness_loader=lambda **_kwargs: (
            calls.append("readiness")
            or {"readiness_digest": "r"}
        ),
        exposure_record_loader=lambda: (
            calls.append("record")
            or {
                "attempt_id": ATTEMPT_1,
                "final_record_digest": "f",
            }
        ),
        completed_exposure_loader=lambda: (
            calls.append("completed") or completed
        ),
    )
    assert calls == ["readiness", "record", "completed"]
    assert value["final_readiness_digest"] == "r"


def test_science_child_gate_order() -> None:
    calls = []
    context = {
        "attempt_id": ATTEMPT_1,
        "launch_digest": "launch",
        "readiness": _readiness_identity(),
    }
    deps = amendment.ChildDependencies(
        entry_gate=lambda: calls.append("entry") or {},
        readiness_loader=lambda **_kwargs: (
            calls.append("readiness") or {}
        ),
        context_validator=lambda _command: (
            calls.append("context") or context
        ),
        worktree_validator=lambda _command: (
            calls.append("worktree") or {}
        ),
        exposure_admission=lambda: (
            calls.append("admission") or {"ok": True}
        ),
        exposure_delegate=lambda: {},
        science_delegate=lambda: calls.append("delegate") or {"ok": True},
    )
    amendment.run_science_child(deps)
    assert calls == [
        "entry",
        "readiness",
        "context",
        "worktree",
        "admission",
        "delegate",
    ]


def test_science_marker_plus_temporary_stops_actual_child_entry(
    tmp_path: Path,
) -> None:
    package = Path("package")
    target = tmp_path / package / "science_started.json"
    target.parent.mkdir(parents=True)
    target.write_text("marker", encoding="utf-8")
    suffix = ".synthetic.atomic.tmp"
    temporary = target.with_name(f".{target.name}{suffix}")
    temporary.write_text("pending", encoding="utf-8")
    namespace = amendment.TemporaryNamespace(
        root=tmp_path,
        package_dir=package,
        suffix=suffix,
        recognizer=lambda path: path == temporary,
    )
    calls = []
    deps = amendment.ChildDependencies(
        entry_gate=lambda: (
            amendment.enforce_entry_temporary_invariants((namespace,))
        ),
        readiness_loader=lambda **_kwargs: (
            calls.append("readiness") or {}
        ),
        context_validator=lambda _command: {},
        worktree_validator=lambda _command: {},
        exposure_admission=lambda: {},
        exposure_delegate=lambda: {},
        science_delegate=lambda: calls.append("environment") or {},
    )
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="ambiguous atomic state.*target=.*temporary=",
    ):
        amendment.run_science_child(deps)
    assert calls == []


def test_temporary_only_is_reserved_for_existing_exact_recovery(
    tmp_path: Path,
) -> None:
    package = Path("package")
    target = tmp_path / package / "science_started.json"
    target.parent.mkdir(parents=True)
    suffix = ".synthetic.atomic.tmp"
    temporary = target.with_name(f".{target.name}{suffix}")
    temporary.write_text("pending", encoding="utf-8")
    namespace = amendment.TemporaryNamespace(
        root=tmp_path,
        package_dir=package,
        suffix=suffix,
        recognizer=lambda path: path == temporary,
    )
    value = amendment.enforce_entry_temporary_invariants((namespace,))
    assert value["pending_count"] == 1
    assert value["pending_exact_recoveries"][0]["target"] == str(target)
    assert not target.exists()


def test_lookalike_temporary_is_rejected(tmp_path: Path) -> None:
    package = Path("package")
    base = tmp_path / package
    base.mkdir()
    suffix = ".synthetic.atomic.tmp"
    temporary = base / f".foreign.json{suffix}"
    temporary.write_text("pending", encoding="utf-8")
    namespace = amendment.TemporaryNamespace(
        root=tmp_path,
        package_dir=package,
        suffix=suffix,
        recognizer=lambda _path: False,
    )
    with pytest.raises(
        amendment.ExecutionLaunchAmendmentError,
        match="unrecognized package temporary",
    ):
        amendment.enforce_entry_temporary_invariants((namespace,))


def test_successful_exposure_record_requires_readiness_and_artifacts() -> None:
    readiness = _readiness_identity()
    artifacts = {"artifact_set_digest": "artifacts"}
    record = {
        "command": "run-exposure",
        "terminal": True,
        "terminal_status": {
            "exit_status": 0,
            "result": "success",
        },
        "launch": {"identity": {"readiness": readiness}},
        "artifact_binding": artifacts,
    }
    amendment.validate_successful_exposure_record(
        record,
        readiness_identity=readiness,
        artifact_binding=artifacts,
    )
    for field, changed in (
        ("readiness", {**readiness, "digest": "changed"}),
        ("artifacts", {"artifact_set_digest": "changed"}),
    ):
        bad = copy.deepcopy(record)
        if field == "readiness":
            bad["launch"]["identity"]["readiness"] = changed
        else:
            bad["artifact_binding"] = changed
        with pytest.raises(amendment.ExecutionLaunchAmendmentError):
            amendment.validate_successful_exposure_record(
                bad,
                readiness_identity=readiness,
                artifact_binding=artifacts,
            )


def test_production_record_paths_are_command_and_attempt_exact() -> None:
    assert amendment.production_record_path(
        "run-exposure", ATTEMPT_1
    ) == (
        amendment.PRODUCTION_RECORD_DIR
        / "run-exposure"
        / f"{ATTEMPT_1}.json"
    )
    with pytest.raises(amendment.ExecutionLaunchAmendmentError):
        amendment.production_record_path("run-exposure", "foreign")


def test_terminal_poll_captures_then_cleans_and_is_idempotent(
    tmp_path: Path,
) -> None:
    _launch(tmp_path, command="service-canary")
    directory = _attempt_dir(tmp_path)
    _write_child_result(directory, command="service-canary")
    cleanup_calls = []
    persisted = []

    def cleanup_runner(argv):
        assert (directory / "terminal.json").is_file()
        cleanup_calls.append(tuple(argv))
        return _completed(argv)

    final = amendment.poll_service_attempt(
        ATTEMPT_1,
        attempt_root=tmp_path / "attempts",
        status_reader=lambda _name: _status(terminal=True),
        cleanup_runner=cleanup_runner,
        cleanup_status_reader=lambda _name: _unloaded_status(),
        readiness_validator=lambda _command: {},
        record_persister=lambda value: (
            persisted.append(copy.deepcopy(dict(value)))
            or tmp_path / "record.json"
        ),
    )
    assert final["terminal"] is True
    assert final["cleanup"]["completed"] is True
    assert [item[2] for item in cleanup_calls] == [
        "stop", "reset-failed"
    ]
    assert len(persisted) == 1
    again = amendment.poll_service_attempt(
        ATTEMPT_1,
        attempt_root=tmp_path / "attempts",
        status_reader=lambda _name: (_ for _ in ()).throw(
            AssertionError("finalized attempt must not query status")
        ),
        cleanup_runner=lambda _argv: (_ for _ in ()).throw(
            AssertionError("finalized attempt must not clean twice")
        ),
        readiness_validator=lambda _command: {},
        record_persister=lambda value: tmp_path / "record.json",
    )
    assert again == final


def test_terminal_poll_preserves_failed_production_attempt(
    tmp_path: Path,
) -> None:
    _launch(tmp_path, command="run-exposure")
    directory = _attempt_dir(tmp_path)
    (directory / "stdout.log").write_bytes(b"")
    (directory / "stderr.log").write_text(
        "interrupted", encoding="utf-8"
    )
    persisted = []
    final = amendment.poll_service_attempt(
        ATTEMPT_1,
        attempt_root=tmp_path / "attempts",
        status_reader=lambda _name: _status(
            terminal=True, code="2", result="signal", status="15"
        ),
        cleanup_runner=lambda argv: _completed(argv),
        cleanup_status_reader=lambda _name: _unloaded_status(),
        readiness_validator=lambda _command: {},
        record_persister=lambda value: (
            persisted.append(copy.deepcopy(dict(value)))
            or tmp_path / "failed.json"
        ),
        artifact_binder=lambda *_args, **_kwargs: (
            (_ for _ in ()).throw(
                AssertionError("failed run has no success artifacts")
            )
        ),
    )
    assert final["terminal_status"]["exit_status"] is None
    assert final["terminal_status"]["signal_status"] == 15
    assert "artifact_binding" not in final
    assert len(persisted) == 1


def test_successful_production_terminal_binds_artifacts(
    tmp_path: Path,
) -> None:
    _launch(tmp_path, command="run-exposure")
    directory = _attempt_dir(tmp_path)
    _write_child_result(directory, command="run-exposure")
    artifacts = {
        "exposure": {"sha256": "e"},
        "artifact_set_digest": "set",
    }
    final = amendment.poll_service_attempt(
        ATTEMPT_1,
        attempt_root=tmp_path / "attempts",
        status_reader=lambda _name: _status(terminal=True),
        cleanup_runner=lambda argv: _completed(argv),
        cleanup_status_reader=lambda _name: _unloaded_status(),
        readiness_validator=lambda _command: {},
        record_persister=lambda _value: tmp_path / "record.json",
        artifact_binder=lambda *_args, **_kwargs: artifacts,
    )
    assert final["artifact_binding"] == artifacts


@pytest.mark.parametrize(
    ("command", "exit_status"),
    (("run-exposure", 15), ("run-science", 0)),
)
def test_repository_preserves_production_terminal_records_and_science_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    exit_status: int,
) -> None:
    monkeypatch.setattr(amendment, "ROOT", tmp_path)
    attempt_id = ATTEMPT_1 if command == "run-exposure" else ATTEMPT_2
    final = {
        "schema_version": "native_v2_terminal_service_record.v1",
        "package_id": amendment.PACKAGE_ID,
        "attempt_id": attempt_id,
        "command": command,
        "launch": {"launch_digest": "launch"},
        "terminal_status": {
            "exit_status": exit_status,
            "result": "success" if exit_status == 0 else "signal",
        },
        "terminal": True,
    }
    if command == "run-science":
        final["artifact_binding"] = {
            "scientific_result": {
                "path": "result.json.gz",
                "sha256": "result-sha",
                "digest": "result-digest",
            },
            "artifact_set_digest": "set",
        }
    final["final_record_digest"] = amendment.digest(final)
    relative = amendment._persist_repository_terminal_record(final)
    assert amendment.load_json(tmp_path / relative) == final
    binding_path = tmp_path / amendment.OUTCOME_RESULT_BINDING_PATH
    if command == "run-science":
        binding = amendment.load_json(binding_path)
        assert binding["attempt_id"] == attempt_id
        assert binding["terminal_record"]["digest"] == (
            final["final_record_digest"]
        )
        assert binding["scientific_result"] == (
            final["artifact_binding"]["scientific_result"]
        )
    else:
        assert not binding_path.exists()


def test_cleanup_records_exit_and_signal_fields_separately(
    tmp_path: Path,
) -> None:
    calls = []

    def runner(argv):
        calls.append(tuple(argv))
        return _completed(argv)

    value = amendment.cleanup_retained_service(
        "unit-name",
        runner=runner,
        status_reader=lambda _name: _unloaded_status(),
    )
    assert value["completed"] is True
    assert [row["action"] for row in value["actions"]] == [
        "stop", "reset-failed"
    ]
    assert calls[0] == (
        "systemctl", "--user", "stop", "unit-name"
    )


def test_cleanup_accepts_exact_already_unloaded_after_successful_stop() -> None:
    service_name = "unit-name"

    def runner(argv):
        if argv[2] == "stop":
            return _completed(argv)
        return _completed(
            argv,
            returncode=1,
            stderr=(
                "Failed to reset failed state of unit "
                f"{service_name}.service: Unit "
                f"{service_name}.service not loaded.\n"
            ),
        )

    value = amendment.cleanup_retained_service(
        service_name,
        runner=runner,
        status_reader=lambda _name: _unloaded_status(),
    )
    assert value["completed"] is True
    assert value["reset_outcome"] == "already_unloaded_after_stop"
    assert value["post_cleanup_status"]["LoadState"] == "not-found"


@pytest.mark.parametrize(
    ("reset_stderr", "post_status"),
    (
        ("different failure\n", _unloaded_status()),
        (
            "Failed to reset failed state of unit unit-name.service: "
            "Unit unit-name.service not loaded.\n",
            _status(terminal=True),
        ),
    ),
)
def test_cleanup_rejects_nonexact_or_still_loaded_reset(
    reset_stderr: str,
    post_status: dict[str, str],
) -> None:
    def runner(argv):
        return (
            _completed(argv)
            if argv[2] == "stop"
            else _completed(argv, returncode=1, stderr=reset_stderr)
        )

    value = amendment.cleanup_retained_service(
        "unit-name",
        runner=runner,
        status_reader=lambda _name: post_status,
    )
    assert value["completed"] is False


def test_no_pre_review_module_global_replacement_or_large_driver_copy() -> None:
    source = Path(amendment.__file__).read_text(encoding="utf-8")
    assert "setattr(prior" not in source
    assert "prior.run_exposure =" not in source
    assert "prior.run_science =" not in source
    assert amendment.production_child_dependencies().exposure_delegate is (
        amendment.prior.run_exposure
    )
    assert amendment.production_child_dependencies().science_delegate is (
        amendment.prior.run_science
    )
